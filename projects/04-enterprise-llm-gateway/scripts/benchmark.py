"""In-process HTTP ASGI benchmark: no socket/network throughput claim."""

import asyncio
import json
import platform
import statistics
import tempfile
import time
from collections import Counter
from pathlib import Path
import httpx
import yaml
from gateway.app import create_app


def percentile(values, q):
    return sorted(values)[max(0, __import__("math").ceil(len(values) * q) - 1)]


async def measure(config, policy, failure=False):
    config = yaml.safe_load(yaml.safe_dump(config))
    config["tenants"]["alpha"].update(
        rpm=10000, tpm=1000000, concurrency=16, budget=1000000, app_budget=1000000
    )
    for model, price in [
        ("economy", 1000000),
        ("quality", 10000000),
        ("fallback", 2000000),
    ]:
        config["models"][model]["price"] = price
    if failure:
        config["models"]["economy"]["behavior"] = "timeout"
    with tempfile.TemporaryDirectory() as temp:
        app = create_app(config, Path(temp) / "state.db")
        durations = []
        statuses = Counter()
        routes = Counter()
        total_cost = 0
        token_total = 0
        fallback = 0
        semaphore = asyncio.Semaphore(8)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://local"
        ) as client:

            async def one(i):
                nonlocal total_cost, token_total, fallback
                async with semaphore:
                    if failure and i == 40:
                        config["models"]["economy"]["behavior"] = "normal"
                    start = time.perf_counter()
                    r = await client.post(
                        "/v1/generate",
                        json=dict(
                            app="chat",
                            prompt="synthetic benchmark",
                            input_tokens=19,
                            max_output_tokens=32,
                            capability="quality" if policy == "quality" else "basic",
                            model=policy,
                        ),
                        headers={"X-API-Key": "demo-alpha", "Idempotency-Key": str(i)},
                    )
                    durations.append(time.perf_counter() - start)
                    statuses[str(r.status_code)] += 1
                    if r.status_code == 200:
                        b = r.json()
                        routes[b["model"]] += 1
                        total_cost += b["cost_micro_usd"]
                        token_total += sum(b["usage"].values())
                        fallback += b["model"] == "fallback"

            start = time.perf_counter()
            await asyncio.gather(*(one(i) for i in range(80)))
            elapsed = time.perf_counter() - start
            metrics = (await client.get("/metrics")).text
        rows = app.state.store.records("requests", "alpha")
        assert sum(r["charged"] for r in rows) == total_cost
        assert sum(statuses.values()) == 80 and sum(routes.values()) == statuses["200"]
        end_of_load_circuit = app.state.breakers[policy].state
        recovery_probe = None
        if failure:
            # A short load run can end before the open circuit cooldown expires.
            # Measure a separate recovery probe without adding it to load metrics.
            await asyncio.sleep(0.11)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://local"
            ) as client:
                probe_start = time.perf_counter()
                probe = await client.post(
                    "/v1/generate",
                    json=dict(
                        app="chat",
                        prompt="synthetic benchmark",
                        input_tokens=19,
                        max_output_tokens=32,
                        model=policy,
                        allow_fallback=False,
                    ),
                    headers={
                        "X-API-Key": "demo-alpha",
                        "Idempotency-Key": "recovery-probe",
                    },
                )
                recovery_probe = {
                    "status": probe.status_code,
                    "elapsed_ms": (time.perf_counter() - probe_start) * 1000,
                    "wait_seconds": 0.11,
                    "model": probe.json().get("model"),
                    "cost_micro_usd": probe.json().get("cost_micro_usd", 0),
                }
            assert (
                recovery_probe["status"] == 200 and recovery_probe["model"] == "economy"
            )
            assert (
                sum(r["charged"] for r in app.state.store.records("requests", "alpha"))
                == total_cost + recovery_probe["cost_micro_usd"]
            )
        # Histogram sums expose actual provider time and gateway elapsed separately.
        sums = {
            line.split(" ")[0]: float(line.split(" ")[1])
            for line in metrics.splitlines()
            if "_sum{" in line and "gateway_latency" in line
        }
        provider_s = sum(v for k, v in sums.items() if "provider_attempt" in k)
        gateway_s = sum(v for k, v in sums.items() if "gateway_total" in k)
        retries = sum(
            float(line.split(" ")[1])
            for line in metrics.splitlines()
            if line.startswith("gateway_events_total{") and 'kind="retry"' in line
        )
        return dict(
            requests=80,
            seconds=elapsed,
            rps=80 / elapsed,
            p50_ms=percentile(durations, 0.5) * 1000,
            p95_ms=percentile(durations, 0.95) * 1000,
            p99_ms=percentile(durations, 0.99) * 1000,
            statuses=dict(statuses),
            routing=dict(routes),
            cost_micro_usd=total_cost,
            actual_tokens=token_total,
            fallbacks=fallback,
            retries=retries,
            error_rate=(80 - statuses["200"]) / 80,
            rejection_rate=sum(statuses.get(str(x), 0) for x in (402, 403, 409, 429))
            / 80,
            estimated_tokens=80 * 51,
            recovery_injection_at_request=40 if failure else None,
            end_of_load_circuit=end_of_load_circuit,
            recovery_probe=recovery_probe,
            final_primary_circuit=app.state.breakers[policy].state,
            provider_attempt_ms_per_request=provider_s / 80 * 1000,
            gateway_overhead_ms_per_request=(gateway_s - provider_s) / 80 * 1000,
            cost_per_success_micro_usd=(
                total_cost / statuses["200"] if statuses["200"] else None
            ),
        )


async def main():
    config = yaml.safe_load(Path("config/example.yaml").read_text())
    report = {
        "environment": {
            "python": platform.python_version(),
            "os": platform.system(),
            "machine": platform.machine(),
            "transport": "HTTPX in-process ASGI",
            "concurrency": 8,
            "requests_per_run": 80,
            "runs_per_scenario": 3,
            "warmup": "none; includes cold state",
            "prices_micro_usd_per_million": {
                "economy": 1000000,
                "quality": 10000000,
                "fallback": 2000000,
            },
            "provider_latency_ms": {"economy": 5, "quality": 10, "fallback": 5},
        },
        "scenarios": {},
    }
    for name, policy, failure in [
        ("economy", "economy", False),
        ("quality", "quality", False),
        ("timeout_recovery", "economy", True),
    ]:
        runs = [await measure(config, policy, failure) for _ in range(3)]
        report["scenarios"][name] = {
            "runs": runs,
            "rps_mean": statistics.mean(r["rps"] for r in runs),
            "rps_stdev": statistics.stdev(r["rps"] for r in runs),
        }
    Path("results/benchmark.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: {"rps_mean": v["rps_mean"], "rps_stdev": v["rps_stdev"]}
                for k, v in report["scenarios"].items()
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
