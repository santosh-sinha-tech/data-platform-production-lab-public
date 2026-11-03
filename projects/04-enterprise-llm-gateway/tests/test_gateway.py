import asyncio
import copy
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import httpx
import pytest
import yaml
from gateway.app import create_app
from gateway.store import Store, Denied
from gateway.providers import Breaker

BODY = dict(app="chat", prompt="hello", input_tokens=5, max_output_tokens=16)


@pytest.fixture
def config():
    return yaml.safe_load(Path("config/example.yaml").read_text())


def run(coro):
    return asyncio.run(coro)


async def exercise(app, bodies, tenant="alpha"):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        return [
            await c.post(
                "/v1/generate",
                json=b,
                headers={"X-API-Key": "demo-" + tenant, "Idempotency-Key": k},
            )
            for k, b in bodies
        ]


def request(app, body=None, key="one", tenant="alpha"):
    return run(exercise(app, [(key, body or BODY)], tenant))[0]


def test_auth_validation_redaction(config, tmp_path, caplog):
    app = create_app(config, tmp_path / "a.db")
    assert request(app, tenant="bad").status_code == 401
    assert request(app, {**BODY, "app": "other"}).status_code == 403
    r = request(app, {**BODY, "prompt": "PRIVATE", "input_tokens": 1})
    assert r.status_code == 422 and "PRIVATE" not in r.text
    r = request(
        app, {**BODY, "prompt": "PRIVATE", "input_tokens": 7, "max_output_tokens": 0}
    )
    assert r.status_code == 422 and "PRIVATE" not in r.text
    assert "PRIVATE" not in caplog.text


def test_routing_and_isolation(config, tmp_path):
    app = create_app(config, tmp_path / "a.db")
    assert request(app).json()["model"] == "economy"
    assert (
        request(app, {**BODY, "capability": "quality"}, key="quality").json()["model"]
        == "quality"
    )
    assert request(app, {**BODY, "model": "quality"}, tenant="beta").status_code == 403
    assert request(app, {**BODY, "cost_ceiling": 0}, key="cheap").status_code == 403
    assert len(app.state.store.records("requests", "beta")) == 0

    async def check():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as c:
            for path in ("usage", "audit"):
                r = await c.get("/v1/" + path, headers={"X-API-Key": "demo-beta"})
                assert (
                    r.json() == []
                    if path == "usage"
                    else all(row["tenant"] == "beta" for row in r.json())
                )

    run(check())


def test_budget_reconcile_idempotency(config, tmp_path):
    config["tenants"]["alpha"].update(budget=1, app_budget=1)
    app = create_app(config, tmp_path / "a.db")
    # Worst permitted route costs one micro-USD; actual also one.
    a = request(app)
    b = request(app)
    assert a.json() == b.json() and app.state.provider.calls["economy"] == 1
    assert request(app, {**BODY, "prompt": "world"}).status_code == 409
    assert request(app, key="two").status_code == 402
    rows = app.state.store.records("requests", "alpha")
    assert len(rows) == 1 and rows[0]["charged"] == 1


def test_refund(config, tmp_path):
    config["models"]["economy"]["price"] = 1000000
    config["models"]["fallback"]["price"] = 1000000
    app = create_app(config, tmp_path / "a.db")
    r = request(app).json()
    assert r["reserved_micro_usd"] == 21 and r["cost_micro_usd"] == 13


def test_atomic_budget(config, tmp_path):
    s = Store(tmp_path / "a.db")
    policy = config["tenants"]["alpha"]
    policy.update(budget=10, app_budget=10, rpm=1000)

    def reserve(i):
        try:
            s.reserve("alpha", "chat", str(i), "hash", "2026-11", 3, 10, policy, 1)
            return True
        except Denied as e:
            assert e.code == "budget_exceeded"
            return False

    with ThreadPoolExecutor(max_workers=16) as pool:
        assert sum(pool.map(reserve, range(30))) == 3


def test_rate_and_concurrency(config, tmp_path):
    config["tenants"]["alpha"]["rpm"] = 1
    app = create_app(config, tmp_path / "a.db")
    assert request(app).status_code == 200
    r = request(app, key="two")
    assert r.status_code == 429 and r.headers["Retry-After"] == "60"
    config["tenants"]["alpha"].update(rpm=100, concurrency=1)
    app = create_app(config, tmp_path / "b.db")

    async def concurrent():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as c:
            return await asyncio.gather(
                *[
                    c.post(
                        "/v1/generate",
                        json=BODY,
                        headers={"X-API-Key": "demo-alpha", "Idempotency-Key": str(i)},
                    )
                    for i in range(8)
                ]
            )

    assert sorted(r.status_code for r in run(concurrent())) == [200] + [429] * 7


@pytest.mark.parametrize("mode", ["timeout", "slow", "429", "500", "unavailable"])
def test_fallback(config, tmp_path, mode):
    config["models"]["economy"]["behavior"] = mode
    app = create_app(config, tmp_path / "a.db")
    r = request(app)
    assert r.status_code == 200 and r.json()["model"] == "fallback"
    assert app.state.provider.calls["economy"] <= 2
    assert request(app, {**BODY, "allow_fallback": False}, key="no").status_code == 503


@pytest.mark.parametrize("mode", ["missing_usage", "incorrect_usage"])
def test_unknown_usage(config, tmp_path, mode):
    config["models"]["economy"]["behavior"] = mode
    app = create_app(config, tmp_path / "a.db")
    assert request(app).json()["error"]["code"] == "unknown_completion"
    assert request(app).status_code == 409
    row = app.state.store.records("requests", "alpha")[0]
    assert row["state"] == "unresolved" and row["charged"] == 0 and row["reserved"] > 0


def test_intermittent(config, tmp_path):
    config["models"]["economy"]["behavior"] = "intermittent"
    app = create_app(config, tmp_path / "a.db")
    assert request(app).status_code == 200 and app.state.provider.calls["economy"] == 2


def test_breaker():
    now = [0.0]
    transitions = []
    b = Breaker(lambda: now[0], transitions.append)
    for _ in range(2):
        b.enter()
        b.result(False)
    assert b.state == "open" and not b.available()
    now[0] = 1
    b.enter()
    assert b.state == "half_open"
    b.result(True)
    assert transitions == ["open", "half_open", "closed"]


def test_restart(config, tmp_path):
    path = tmp_path / "a.db"
    app = create_app(config, path)
    s = app.state.store
    s.reserve(
        "alpha",
        "chat",
        "unfinished",
        "hash",
        config["period"],
        1,
        21,
        config["tenants"]["alpha"],
        1,
    )
    app = create_app(config, path)
    assert s.records("requests", "alpha")[0]["state"] == "unresolved"
    with pytest.raises(Denied) as e:
        s.reserve(
            "alpha",
            "chat",
            "unfinished",
            "hash",
            config["period"],
            1,
            21,
            config["tenants"]["alpha"],
            1,
        )
    assert e.value.code == "unresolved"


def test_metrics(config, tmp_path):
    app = create_app(config, tmp_path / "a.db")
    request(app)

    async def check():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as c:
            r = await c.get("/metrics")
            assert "gateway_tokens_total" in r.text
            assert "hello" not in r.text and "request_id=" not in r.text

    run(check())


def test_deadline(config, tmp_path):
    config["models"]["economy"]["behavior"] = "timeout"
    app = create_app(config, tmp_path / "a.db")
    assert request(app, {**BODY, "timeout": 0.01}).status_code == 503
    assert app.state.store.records("requests", "alpha")[0]["state"] == "released"


def test_tpm(config, tmp_path):
    config["tenants"]["alpha"]["tpm"] = 20
    app = create_app(config, tmp_path / "a.db")
    assert request(app).status_code == 429


def test_benchmark_calculations():
    import importlib.util

    spec = importlib.util.spec_from_file_location("bench", "scripts/benchmark.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.percentile([1, 2, 3, 4], 0.5) == 2
    assert mod.percentile(list(range(100)), 0.99) == 98


def test_same_key_concurrently(config, tmp_path):
    config["models"]["economy"]["timeout"] = 1
    app = create_app(config, tmp_path / "a.db")

    async def duplicate():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as c:
            return await asyncio.gather(
                *[
                    c.post(
                        "/v1/generate",
                        json={**BODY, "timeout": 2},
                        headers={"X-API-Key": "demo-alpha", "Idempotency-Key": "same"},
                    )
                    for _ in range(12)
                ]
            )

    results = run(duplicate())
    assert sum(r.status_code == 200 for r in results) >= 1
    assert all(r.status_code in (200, 409) for r in results)
    assert app.state.provider.calls["economy"] == 1
    assert sum(r["charged"] for r in app.state.store.records("requests", "alpha")) == 1


def test_quality_fallback_and_availability(config, tmp_path):
    config["models"]["quality"]["behavior"] = "unavailable"
    app = create_app(config, tmp_path / "a.db")
    assert request(app, {**BODY, "capability": "quality"}).status_code == 503
    assert "fallback" not in app.state.provider.calls
    config["models"]["economy"]["available"] = False
    app = create_app(config, tmp_path / "b.db")
    assert request(app).json()["model"] == "fallback"


def test_cancel_keeps_hold(config, tmp_path):
    config["models"]["economy"]["latency"] = 1
    app = create_app(config, tmp_path / "a.db")

    async def cancel():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as c:
            task = asyncio.create_task(
                c.post(
                    "/v1/generate",
                    json=BODY,
                    headers={"X-API-Key": "demo-alpha", "Idempotency-Key": "cancel"},
                )
            )
            while not app.state.provider.calls:
                await asyncio.sleep(0.001)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    run(cancel())
    assert app.state.store.records("requests", "alpha")[0]["state"] == "unresolved"


def test_breaker_probe_exclusion():
    from gateway.providers import ProviderError

    now = [0.0]
    b = Breaker(lambda: now[0], lambda s: None)
    b.result(False)
    b.result(False)
    now[0] = 1
    b.enter()
    with pytest.raises(ProviderError):
        b.enter()
    b.result(False)
    assert b.state == "open"


def test_unsafe_timeout_never_retries(config, tmp_path):
    config["models"]["economy"]["behavior"] = "timeout"
    app = create_app(config, tmp_path / "a.db")
    app.state.provider.replay_safe = False
    assert request(app).status_code == 503
    assert app.state.provider.calls == {"economy": 1}
    assert app.state.store.records("requests", "alpha")[0]["state"] == "unresolved"


def test_audit_and_log_redaction(config, tmp_path, caplog):
    app = create_app(config, tmp_path / "a.db")
    assert (
        request(
            app, {**BODY, "prompt": "PRIVATE-CONTENT", "input_tokens": 15}
        ).status_code
        == 200
    )
    audits = app.state.store.records("audits", "alpha")
    assert "PRIVATE-CONTENT" not in json.dumps(audits)
    assert "PRIVATE-CONTENT" not in caplog.text
    assert "request_id" in caplog.text


def test_application_budget(config, tmp_path):
    config["tenants"]["alpha"].update(budget=10, app_budget=1)
    app = create_app(config, tmp_path / "a.db")
    assert request(app).status_code == 200
    assert request(app, key="next").status_code == 402
    assert request(app, {**BODY, "app": "batch"}).status_code == 200


def test_reconciliation_and_settlement_cas(config, tmp_path):
    import subprocess, sys

    db = tmp_path / "a.db"
    app = create_app(config, db)
    s = app.state.store
    policy = config["tenants"]["alpha"]
    s.reserve("alpha", "chat", "unknown", "hash", config["period"], 5, 20, policy, 1)
    s.finish("alpha", "chat", "unknown", "unresolved")
    s.finish("alpha", "chat", "unknown", "completed", 5, {})
    assert s.records("requests", "alpha")[0]["state"] == "unresolved"
    cmd = [
        sys.executable,
        "scripts/reconcile.py",
        "--db",
        str(db),
        "--tenant",
        "alpha",
        "--app",
        "chat",
        "--key",
        "unknown",
        "--charge",
        "3",
        "--evidence",
        "synthetic-case-001",
    ]
    assert subprocess.run(cmd, capture_output=True).returncode == 0
    assert subprocess.run(cmd, capture_output=True).returncode != 0
    row = s.records("requests", "alpha")[0]
    assert row["state"] == "reconciled" and row["charged"] == 3
    with pytest.raises(Denied):
        s.reserve(
            "alpha", "chat", "unknown", "hash", config["period"], 5, 20, policy, 1
        )


def test_breaker_ignores_stale_completions():
    now = [0.0]
    b = Breaker(lambda: now[0], lambda s: None)
    old = b.enter()
    b.result(False, old)
    second = b.enter()
    b.result(False, second)
    assert b.state == "open"
    b.result(True, old)
    assert b.state == "open"
    now[0] = 1
    probe = b.enter()
    b.result(True, old)
    assert b.state == "half_open"
    b.result(True, probe)
    assert b.state == "closed"


def test_configured_input_limit(config, tmp_path):
    config["limits"]["input_chars"] = 3
    app = create_app(config, tmp_path / "a.db")
    assert request(app).json()["error"]["code"] == "input_too_large"


def test_unexpected_provider_error_is_redacted(config, tmp_path, caplog):
    app = create_app(config, tmp_path / "a.db")

    async def broken(*args):
        raise RuntimeError("PRIVATE-CONTENT")

    app.state.provider.generate = broken
    r = request(app)
    assert r.status_code == 500 and r.json()["error"]["code"] == "internal_error"
    assert "PRIVATE-CONTENT" not in r.text + caplog.text
    assert app.state.store.records("requests", "alpha")[0]["state"] == "unresolved"


def test_cost_attribution_and_utilization(config, tmp_path):
    config["models"]["economy"]["price"] = 1000000
    config["models"]["fallback"]["price"] = 2000000
    config["models"]["economy"]["behavior"] = "unavailable"
    app = create_app(config, tmp_path / "a.db")
    r = request(app).json()
    assert r["cost_micro_usd"] == 26

    async def check():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as c:
            cost = (
                await c.get("/v1/costs", headers={"X-API-Key": "demo-alpha"})
            ).json()
            assert cost["charged"] == 26 and cost["held"] == 0
            assert cost["by_model"]["fallback"] == 26
            assert cost["fallback_delta"] == 13 and cost["cost_per_success"] == 26
            assert cost["utilization"] == 26 / config["tenants"]["alpha"]["budget"]
            other = (
                await c.get("/v1/costs", headers={"X-API-Key": "demo-beta"})
            ).json()
            assert other["charged"] == 0

    run(check())
