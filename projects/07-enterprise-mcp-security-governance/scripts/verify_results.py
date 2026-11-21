"""Cross-check result artifacts against their labeled fixtures and run totals."""

import csv
import json
import math
import sys
from pathlib import Path

from mcp_governance.metrics import latency, prometheus, summarize
from mcp_governance.scenarios import LABELS

root = Path(sys.argv[1])
metrics = json.loads((root / "metrics.json").read_text())
with (root / "scenario_comparison.csv").open(newline="") as file:
    rows = list(csv.DictReader(file))

assert rows
repeats = {row["repeat"] for row in rows}
assert len(repeats) == {"quick": 2, "full": 3}[metrics["mode"]]
assert len(rows) == len(repeats) * len(LABELS)
assert {(row["repeat"], row["case"]) for row in rows} == {
    (repeat, case) for repeat in repeats for case in LABELS
}
for row in rows:
    _, expected, effects = LABELS[row["case"]]
    assert row["expected"] == row["outcome"] == expected
    assert int(row["effects"]) == effects
    assert row["audit_outcomes"].split("|")[-1] == expected
    for key in ("passed", "audit_complete"):
        assert row[key] == "True"
        row[key] = True
    row["approval_wait_ms"] = float(row["approval_wait_ms"]) if row["approval_wait_ms"] else None
    assert row["correlation"]
assert len({row["correlation"] for row in rows}) == len(rows)

for key, value in summarize(rows).items():
    assert metrics[key] == value, key
assert (root / "metrics.prom").read_text() == prometheus(metrics)
with (root / "latency_samples.csv").open(newline="") as file:
    samples = list(csv.DictReader(file))
runs = metrics["benchmark_runs"]
assert len(runs) == len(repeats)
for run in runs:
    assert run["requests"] == {"quick": 40, "full": 300}[metrics["mode"]]
    assert math.isclose(run["calls_per_second"], run["requests"] / run["seconds"])
    run_samples = [float(row["total_ms"]) for row in samples
                   if int(row["repeat"]) == run["repeat"]]
    assert len(run_samples) == run["requests"]
    assert run["total_ms"] == latency(run_samples)
total = sum(run["requests"] for run in runs)
assert math.isclose(metrics["benchmark_calls_per_second"],
                    total / sum(run["seconds"] for run in runs))
assert len(samples) == total
for name, summary in metrics["benchmark_latency_ms"].items():
    assert summary == latency(float(row[name]) for row in samples)
    assert summary["n"] == total
    assert summary["min"] <= summary["p50"] <= summary["p95"] <= summary["p99"] <= summary["max"]
    assert summary["min"] <= summary["mean"] <= summary["max"]
print(f"Verified {len(rows)} scenario rows and {total} measured calls across {len(runs)} runs.")
