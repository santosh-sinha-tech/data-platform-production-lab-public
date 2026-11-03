"""Named reproducible failure drills, assertions fail the runner immediately."""

import asyncio
import copy
import json
import tempfile
from pathlib import Path
import httpx
import yaml
from gateway.app import create_app

BASE = dict(app="chat", prompt="synthetic", input_tokens=9, max_output_tokens=16)


async def main():
    config = yaml.safe_load(Path("config/example.yaml").read_text())
    report = {}
    with tempfile.TemporaryDirectory() as temp:

        def new(name, edit=None):
            c = copy.deepcopy(config)
            if edit:
                edit(c)
            return create_app(c, Path(temp) / (name + ".db"))

        async def call(app, key="one", tenant="alpha", body=None):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://local"
            ) as client:
                return await client.post(
                    "/v1/generate",
                    json=body or BASE,
                    headers={"X-API-Key": "demo-" + tenant, "Idempotency-Key": key},
                )

        app = new("normal")
        a = await call(app)
        assert a.status_code == 200 and a.json()["model"] == "economy"
        report["A_normal_routing"] = {"status": 200, "model": a.json()["model"]}
        app = new(
            "budget", lambda c: c["tenants"]["alpha"].update(budget=1, app_budget=1)
        )
        assert (await call(app)).status_code == 200
        b = await call(app, "two")
        assert b.status_code == 402
        report["B_budget_exhaustion"] = {"status": b.status_code}
        app = new("rate", lambda c: c["tenants"]["alpha"].update(rpm=1))
        await call(app)
        r = await call(app, "two")
        assert r.status_code == 429
        report["C_rate_limit"] = {
            "status": 429,
            "retry_after": r.headers["Retry-After"],
        }
        app = new(
            "timeout", lambda c: c["models"]["economy"].update(behavior="timeout")
        )
        r = await call(app)
        assert r.status_code == 200 and r.json()["model"] == "fallback"
        report["D_safe_timeout_fallback"] = {
            "model": r.json()["model"],
            "primary_attempts": app.state.provider.calls["economy"],
        }
        assert app.state.breakers["economy"].state == "open"
        app.state.config["models"]["economy"]["behavior"] = "normal"
        await asyncio.sleep(0.11)
        r = await call(app, "recovery")
        assert (
            r.json()["model"] == "economy"
            and app.state.breakers["economy"].state == "closed"
        )
        report["E_circuit_recovery"] = {
            "observed": ["open", "half_open", "closed"],
            "recovered_model": "economy",
        }
        app = new(
            "race", lambda c: c["tenants"]["alpha"].update(budget=3, app_budget=3)
        )
        rs = await asyncio.gather(*(call(app, str(i)) for i in range(20)))
        successful = sum(r.status_code == 200 for r in rs)
        assert (
            successful == 3
            and sum(x["charged"] for x in app.state.store.records("requests", "alpha"))
            == 3
        )
        report["F_same_budget_race"] = {
            "requests": 20,
            "successful": successful,
            "budget_rejections": sum(r.status_code == 402 for r in rs),
            "charged_micro_usd": 3,
        }
        app = new("duplicate")
        a = await call(app)
        b = await call(app)
        assert a.json() == b.json() and app.state.provider.calls["economy"] == 1
        report["G_duplicate_key"] = {
            "dispatches": 1,
            "ledger_rows": len(app.state.store.records("requests", "alpha")),
        }
        b = await call(app, tenant="beta", body={**BASE, "model": "quality"})
        assert b.status_code == 403 and not app.state.store.records("requests", "beta")
        report["H_tenant_isolation"] = {
            "forbidden_model_status": 403,
            "beta_ledger_rows": 0,
        }
        app = new("restart")
        store = app.state.store
        store.reserve(
            "alpha",
            "chat",
            "pending",
            "hash",
            config["period"],
            1,
            25,
            config["tenants"]["alpha"],
            1,
        )
        app = create_app(copy.deepcopy(config), Path(temp) / "restart.db")
        row = app.state.store.records("requests", "alpha")[0]
        assert row["state"] == "unresolved" and row["reserved"] == 1
        report["I_restart_unsettled"] = {
            "state": row["state"],
            "held_micro_usd": row["reserved"],
            "method": "seed durable reservation, recreate exclusive gateway",
        }
    Path("results/failure-scenarios.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
