"""Recompute aggregate results independently from retained per-scenario samples."""

import csv
import json
import math
import sys
from pathlib import Path

p = Path(sys.argv[1] if len(sys.argv) > 1 else "results")
m = json.loads((p / "metrics.json").read_text())
r = m["records"]
s = m["summary"]
assert (
    len(r)
    == m["runs"] * m["repeats_per_scenario_per_run"] * m["scenario_count"]
    == s["samples"]
)
assert sum(x["passed"] for x in r) == m["scenario_passes"] == len(r)
assert abs(sum(x["cost"] for x in r) - s["simulated_execution_cost"]) < 1e-9
assert sum(x["attempts"] for x in r) == s["attempts"]
assert (
    abs(sum(x["actual"] == "succeeded" for x in r) / len(r) - s["success_rate"]) < 1e-12
)
for q in (0.5, 0.95, 0.99):
    value = sorted(x["latency_seconds"] for x in r)[math.ceil(q * len(r)) - 1]
    assert value == s["latency_seconds"][f"p{int(q * 100)}"]
assert (
    abs(
        len(r) / sum(x["wall_seconds"] for x in m["per_run"])
        - s["throughput_workflows_per_second"]
    )
    < 1e-9
)
assert all(x["pass"] for x in m["policy_cases"])
rows = list(csv.DictReader((p / "scenario_comparison.csv").open()))
assert len(rows) == m["scenario_count"]
assert all(int(x["samples"]) == int(x["passes"]) for x in rows)
print(f"Verified {len(r)} samples, arithmetic and {len(rows)} scenario outcomes")

obs = [o for x in r for o in x["observations"]]


def values(name):
    return [o["value"] for o in obs if o["name"] == name]


for q in (0.5, 0.95, 0.99):
    tool = sorted(values("tool_latency"))
    assert (
        tool[math.ceil(q * len(tool)) - 1]
        == s["tool_latency_seconds"][f"p{int(q * 100)}"]
    )
for event, key in [
    ("retry", "retry_count"),
    ("duplicate", "duplicate_suppressed"),
    ("step_failure", "step_failure_count"),
    ("approval_wait", "approval_wait_simulated_seconds"),
]:
    assert sum(values(event)) == s[key]
assert len(values("recovery")) == s["recovery_samples"]
assert sum(values("recovery")) / len(values("recovery")) == s["recovery_success_rate"]
assert len(obs) == s["telemetry_events"]
print(
    "Verified tool quantiles, retry/duplicate/failure/wait counts and recovery denominator"
)

assert sum(x["attempted_steps"] for x in r)==s["attempted_distinct_steps"]
assert s["attempts"]/s["attempted_distinct_steps"]==s["retry_amplification"]
c=m["cost_model"]; prices=c["prices"]
assert c["planning_calls_simulated"]==sum(x["cost"]>0 for x in r)
assert abs(c["planning_calls_simulated"]*prices["planning"]+s["attempts"]*prices["tool"]-s["simulated_execution_cost"])<1e-9
assert c["state_writes_proxy"]==s["attempts"]*5+c["planning_calls_simulated"]*4
assert c["audit_cost_proxy"]==s["audit_bytes_proxy"]*prices["audit_byte"]
print("Verified simulated planning, tool and infrastructure cost calculations")
