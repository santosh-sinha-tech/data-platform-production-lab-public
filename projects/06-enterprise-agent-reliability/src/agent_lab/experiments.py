"""Deterministic scenario outcomes; measured wall-clock benchmark variability."""

import argparse
import csv
import json
import math
import platform
import statistics
import tempfile
import time
from pathlib import Path
from .engine import Engine
from .config import config_path
from .models import Identity, Request, Action, Denied, NotFound, Interrupted

OP = Identity(tenant="alpha", subject="operator-a", role="operator")
APPROVER = Identity(tenant="alpha", subject="approver-a", role="approver")
BETA = Identity(tenant="beta", subject="approver-b", role="approver")
READER = Identity(tenant="alpha", subject="reader-a", role="reader")


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


FIXTURES = json.loads(
    config_path("scenarios.json").read_text()
)
SCENARIOS = [(f["code"], f["label"], f["expected"]) for f in FIXTURES]


def custom(key, tool, fault="none"):
    return Request(key=key, workflow="custom", actions=[Action(tool=tool, fault=fault)])


def scenario(code, path):
    clock = Clock()
    fixture = next(f for f in FIXTURES if f["code"] == code)
    config = {"backoff_seconds": 0.0001, **fixture["config"]}
    e = Engine(path, config, clock=clock)
    request = Request.model_validate(fixture["request"])
    identity = READER if fixture["identity"] == "reader" else OP
    control = fixture["control"]
    started = time.perf_counter()
    try:
        try:
            row = e.submit(identity, request)
        except Interrupted:
            eid = e.db.execute("SELECT id FROM executions").fetchone()[0]
            e.store.close()
            e = Engine(path, config, clock=clock)
            row = e.recover(eid, OP)
        if control == "duplicate":
            original = row["id"]
            row = e.submit(OP, request)
            # Calling completed executor again must not call tools.
            row = e.run(original, OP)
            assert row["id"] == original
        if control in {
            "approve",
            "reject",
            "expire",
            "approve_reconcile",
            "cross_tenant",
        }:
            assert row["status"] == "pending_approval"
            if control == "expire":
                clock.advance(61)
                row = e.recover(row["id"], OP)
            else:
                clock.advance(2)
                row = e.approve(
                    row["id"],
                    BETA if control == "cross_tenant" else APPROVER,
                    "rejected" if control == "reject" else "approved",
                )
        if control == "approve_reconcile":
            assert row["status"] == "unknown"
            row = e.reconcile(row["id"], OP)
        if control == "compensate":
            e.compensate(row["id"], 0, OP)
        actual = row["status"]
    except (Denied, NotFound):
        actual = "denied"
        e.metric("admission", "policy_denial")
        e.event("admission", "policy_denial")
        e.db.commit()
    elapsed = time.perf_counter() - started
    observations = [
        dict(r) for r in e.db.execute("SELECT name,tool,value FROM observations")
    ]
    effects = e.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0]
    attempts = e.db.execute("SELECT COALESCE(SUM(attempts),0) FROM steps").fetchone()[0]
    steps = e.db.execute("SELECT COUNT(*) FROM steps").fetchone()[0]
    attempted_steps = e.db.execute("SELECT COUNT(*) FROM steps WHERE attempts>0").fetchone()[0]
    cost = e.db.execute("SELECT COALESCE(SUM(cost),0) FROM executions").fetchone()[0]
    audit_bytes = e.db.execute(
        "SELECT COALESCE(SUM(length(detail)+length(event)),0) FROM audit"
    ).fetchone()[0]
    audits = [
        dict(r)
        for r in e.db.execute("SELECT execution,event,detail FROM audit ORDER BY seq")
    ]
    if code == "L":
        assert effects == 0 and "synthetic-private-value" not in json.dumps(audits)
    e.store.close()
    return {
        "code": code,
        "actual": actual,
        "latency_seconds": elapsed,
        "observations": observations,
        "effects": effects,
        "attempts": attempts,
        "steps": steps,
        "attempted_steps": attempted_steps,
        "cost": cost,
        "audit_bytes": audit_bytes,
        "audit_events": len(audits),
        "audit": audits,
    }


def percentile(values, q):
    if not values:
        return 0.0
    return sorted(values)[max(0, math.ceil(len(values) * q) - 1)]


def summarize(records, wall):
    observations = [o for r in records for o in r["observations"]]

    def vals(name):
        return [o["value"] for o in observations if o["name"] == name]

    latency = [r["latency_seconds"] for r in records]
    recovery = vals("recovery")
    attempts = sum(r["attempts"] for r in records)
    retries = sum(vals("retry"))
    # Includes crash replay: attempts minus attempted distinct steps, separately
    # from classified transient retries.
    attempted_steps = sum(r["attempted_steps"] for r in records)
    return {
        "samples": len(records),
        "wall_seconds": wall,
        "throughput_workflows_per_second": len(records) / wall,
        "latency_seconds": {
            f"p{int(q * 100)}": percentile(latency, q) for q in (0.5, 0.95, 0.99)
        },
        "success_rate": sum(r["actual"] == "succeeded" for r in records) / len(records),
        "tool_latency_seconds": {
            f"p{int(q * 100)}": percentile(vals("tool_latency"), q)
            for q in (0.5, 0.95, 0.99)
        },
        "approval_wait_simulated_seconds": sum(vals("approval_wait")),
        "retry_count": retries,
        "attempts": attempts,
        "attempted_distinct_steps": attempted_steps,
        "retry_amplification": attempts / attempted_steps if attempted_steps else 0,
        "duplicate_suppressed": sum(vals("duplicate")),
        "step_failure_count": sum(vals("step_failure")),
        "step_failure_rate_per_attempt": sum(vals("step_failure")) / attempts,
        "recovery_success_rate": sum(recovery) / len(recovery) if recovery else None,
        "recovery_samples": len(recovery),
        "simulated_execution_cost": sum(r["cost"] for r in records),
        "audit_bytes_proxy": sum(r["audit_bytes"] for r in records),
        "audit_events": sum(r["audit_events"] for r in records),
        "telemetry_events": len(observations),
    }


def policy_cases():
    from .policy import authorize

    cfg = {"max_steps": 8}
    labels = [
        ("read allowed", READER, "alpha", [Action(tool="read_quality")], True),
        ("write denied", READER, "alpha", [Action(tool="create_ticket")], False),
        ("tenant denied", OP, "beta", [Action(tool="read_quality")], False),
        ("operator write", OP, "alpha", [Action(tool="create_ticket")], True),
        ("unknown denied", OP, "alpha", [Action(tool="unknown")], False),
        ("depth denied", OP, "alpha", [Action(tool="read_quality")] * 9, False),
        (
            "combination denied",
            OP,
            "alpha",
            [Action(tool="update_deployment"), Action(tool="rerun_pipeline")],
            False,
        ),
    ]
    out = []
    for label, who, tenant, actions, expected in labels:
        try:
            for action in actions:
                authorize(who, tenant, action, actions, cfg)
            actual = True
        except Denied:
            actual = False
        out.append(
            {
                "label": label,
                "expected_allow": expected,
                "actual_allow": actual,
                "pass": actual == expected,
            }
        )
    return out


def run(mode, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    runs, repeats = (2, 2) if mode == "quick" else (3, 20)
    records = []
    summaries = []
    with tempfile.TemporaryDirectory() as temp:
        # Excluded warm-up includes SQLite schema and Python code paths.
        scenario("A", Path(temp) / "warmup.db")
        for run_id in range(runs):
            batch = []
            started = time.perf_counter()
            for repeat in range(repeats):
                for code, _, expected in SCENARIOS:
                    record = scenario(code, Path(temp) / f"{run_id}-{repeat}-{code}.db")
                    record.update(
                        run=run_id,
                        repeat=repeat,
                        expected=expected,
                        passed=record["actual"] == expected,
                    )
                    batch.append(record)
            summaries.append(summarize(batch, time.perf_counter() - started))
            records.extend(batch)
    totals = summarize(records, sum(s["wall_seconds"] for s in summaries))
    cases = policy_cases()
    prices = json.loads(config_path("example.yaml").read_text())["prices"]
    planning_calls = sum(r["cost"]>0 for r in records)
    state_writes_proxy = totals["attempts"]*5 + planning_calls*4
    cost_model = {
        "prices": prices, "planning_calls_simulated": planning_calls, "real_provider_calls": 0,
        "state_writes_proxy": state_writes_proxy,
        "state_cost_proxy": state_writes_proxy*prices["state_write"],
        "audit_cost_proxy": totals["audit_bytes_proxy"]*prices["audit_byte"],
        "telemetry_cost_proxy": totals["telemetry_events"]*prices["telemetry_event"],
        "retry_and_replay_cost": (totals["attempts"]-totals["attempted_distinct_steps"])*prices["tool"],
    }
    metrics = {
        "mode": mode,
        "cost_model": cost_model,
        "environment": {
            "python": platform.python_version(),
            "os": platform.system(),
            "machine": platform.machine(),
            "sqlite": __import__("sqlite3").sqlite_version,
            "workers": 1,
            "concurrency": 1,
        },
        "runs": runs,
        "repeats_per_scenario_per_run": repeats,
        "scenario_count": len(SCENARIOS),
        "summary": totals,
        "per_run": summaries,
        "policy_cases": cases,
        "policy_accuracy": sum(c["pass"] for c in cases) / len(cases),
        "scenario_passes": sum(r["passed"] for r in records),
        "variability": {
            "throughput_stdev": statistics.stdev(
                s["throughput_workflows_per_second"] for s in summaries
            ),
            "p95_latency_stdev": statistics.stdev(
                s["latency_seconds"]["p95"] for s in summaries
            ),
        },
        "records": [{k: v for k, v in r.items() if k != "audit"} for r in records],
    }
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    with (output / "scenario_comparison.csv").open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["code", "scenario", "expected", "actual", "samples", "passes"])
        for code, label, expected in SCENARIOS:
            group = [r for r in records if r["code"] == code]
            writer.writerow(
                [
                    code,
                    label,
                    expected,
                    group[0]["actual"],
                    len(group),
                    sum(r["passed"] for r in group),
                ]
            )
    (output / "audit_example.jsonl").write_text(
        "\n".join(json.dumps(a) for a in records[0]["audit"]) + "\n"
    )
    report = f"""# Executed local simulated benchmark

Mode: {mode}. {runs} repeated runs using a fresh database for every scenario sample × {repeats} repetitions × {len(SCENARIOS)} scenarios = {len(records)} attempts; one excluded warm-up. Single serial worker; SQLite WAL; no HTTP network, model inference or external tool calls. Environment: `{json.dumps(metrics["environment"], sort_keys=True)}`. Database creation/checkpoint/close overhead is included in throughput wall time; workflow percentiles time submit/control operations after schema initialization. These populations differ intentionally.

- Throughput: {totals["throughput_workflows_per_second"]:.2f} scenario attempts/s; between-run sample standard deviation {metrics["variability"]["throughput_stdev"]:.2f}.
- Active workflow latency p50/p95/p99: {totals["latency_seconds"]["p50"]:.6f}/{totals["latency_seconds"]["p95"]:.6f}/{totals["latency_seconds"]["p99"]:.6f} seconds. p95 between-run standard deviation {metrics["variability"]["p95_latency_stdev"]:.6f} seconds.
- Tool latency p50/p95/p99: {totals["tool_latency_seconds"]["p50"]:.6f}/{totals["tool_latency_seconds"]["p95"]:.6f}/{totals["tool_latency_seconds"]["p99"]:.6f} seconds.
- Workflow success: {totals["success_rate"]:.2%}; includes deliberately denied/failed scenarios. Expected scenario outcomes: {metrics["scenario_passes"]}/{len(records)}.
- Recovery success: {totals["recovery_success_rate"]:.2%} over {totals["recovery_samples"]} crash-replay/reconciliation samples.
- Retry amplification: {totals["retry_amplification"]:.4f} attempts per attempted distinct step; {totals["retry_count"]} scheduled classified retries (including retries subsequently denied by budget). Crash replay included separately in amplification.
- Duplicate request suppression: {totals["duplicate_suppressed"]:.0f}; each duplicate test asserts the original execution ID and tests verify side-effect count.
- Policy accuracy: {metrics["policy_accuracy"]:.2%} on {len(cases)} hand-labeled finite cases; no claim of arbitrary-policy correctness.
- Approval waits: {totals["approval_wait_simulated_seconds"]:.0f} virtual seconds, excluded from wall-clock latency. This is a clock-driven expiration experiment, not measured human response time.
- Simulated planning/tool cost: {totals["simulated_execution_cost"]:.6f} units. No provider charges. Persistence and telemetry proxies described in architecture.

Infrastructure cost proxies: {json.dumps(cost_model, sort_keys=True)}. Logical state mutations use the documented sizing proxy, not measured disk I/O. Audit bytes are payload-only and telemetry is counted events, not observed network traffic.

The Docker/host scheduler and background workloads are uncontrolled; do not compare these samples as isolated hardware capacity.

No production-scale, network, concurrent-worker, external exactly-once or prompt-injection-proof claim follows from these results. Durations vary with host scheduling, filesystem caching and virtualization. Decisions, counts and simulated cost reproduce; timestamps, execution IDs and latency do not.
"""
    (output / "benchmark_report.md").write_text(report)
    (output / "failure_analysis.md").write_text(
        "# Failure injection outcomes\n\nAll fixtures are synthetic. See scenario_comparison.csv for expected and executed outcomes.\n\n"
        + "\n".join(
            f"- {code}: {label}; expected {expected}; {sum(r['passed'] for r in records if r['code'] == code)}/{sum(r['code'] == code for r in records)} matched."
            for code, label, expected in SCENARIOS
        )
        + "\n\nJ closes and reopens SQLite after an injected exception at the effect/receipt boundary. The subprocess kill test separately exercises real abrupt process death. I never repeats the rerun: reconciliation reads the simulator ledger. G exhausts two retries; K fails on retry cost admission. O compensates only the completed reversible ticket. Failure does not imply automatic rollback of all effects.\n"
    )
    assert all(r["passed"] for r in records)
    assert all(c["pass"] for c in cases)
    print(
        json.dumps(
            {
                "samples": len(records),
                "passed": metrics["scenario_passes"],
                "summary": totals,
            },
            indent=2,
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["quick", "full"], default="quick")
    parser.add_argument("--output", default="runtime/quick")
    args = parser.parse_args()
    run(args.mode, args.output)


if __name__ == "__main__":
    main()
