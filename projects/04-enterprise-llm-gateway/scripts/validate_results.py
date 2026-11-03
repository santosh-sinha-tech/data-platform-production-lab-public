"""Independently validate report arithmetic and named scenario invariants."""

import json
import math
import statistics
from pathlib import Path

b = json.loads(Path("results/benchmark.json").read_text())
for scenario in b["scenarios"].values():
    runs = scenario["runs"]
    assert len(runs) == 3
    assert math.isclose(scenario["rps_mean"], statistics.mean(r["rps"] for r in runs))
    assert math.isclose(scenario["rps_stdev"], statistics.stdev(r["rps"] for r in runs))
    for r in runs:
        assert r["requests"] == sum(r["statuses"].values()) == 80
        assert sum(r["routing"].values()) == r["statuses"].get("200", 0)
        assert math.isclose(r["rps"], 80 / r["seconds"])
        assert 0 <= r["p50_ms"] <= r["p95_ms"] <= r["p99_ms"]
        assert r["actual_tokens"] == 27 * sum(r["routing"].values())
        expected = sum(
            n
            * math.ceil(
                27 * b["environment"]["prices_micro_usd_per_million"][m] / 1000000
            )
            for m, n in r["routing"].items()
        )
        assert r["cost_micro_usd"] == expected
        if r["statuses"].get("200"):
            assert math.isclose(
                r["cost_per_success_micro_usd"], expected / r["statuses"]["200"]
            )
f = json.loads(Path("results/failure-scenarios.json").read_text())
assert len(f) == 9
assert f["F_same_budget_race"]["charged_micro_usd"] == 3
assert f["G_duplicate_key"]["dispatches"] == 1
assert f["I_restart_unsettled"]["state"] == "unresolved"
print(
    "PASS: benchmark arithmetic, attribution, variability and nine scenario invariants"
)
