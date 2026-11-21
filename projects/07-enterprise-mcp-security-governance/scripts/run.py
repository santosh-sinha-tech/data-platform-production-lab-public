"""Run labeled scenarios and warm-session benchmarks into a chosen directory."""

import argparse
import asyncio
import csv
import json
import platform
import sqlite3
import tempfile
from importlib.metadata import version
from pathlib import Path

from mcp_governance.metrics import latency, prometheus, summarize
from mcp_governance.scenarios import LABELS, benchmark, run_case

MODES = {"quick": (2, 2, 40, 1), "full": (3, 3, 300, 4)}


async def run(mode, output):
    scenario_runs, benchmark_runs, count, concurrency = MODES[mode]
    cases, all_samples, runs = [], [], []
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        for repeat in range(1, scenario_runs + 1):
            for label in LABELS:
                case = await run_case(label, root / f"{repeat}-{label}.sqlite")
                cases.append({"repeat": repeat, **case})
        for repeat in range(1, benchmark_runs + 1):
            samples, elapsed = await benchmark(root / f"bench-{repeat}.sqlite", count, concurrency)
            runs.append({"repeat": repeat, "requests": count, "seconds": elapsed,
                         "calls_per_second": count / elapsed,
                         "total_ms": latency(sample["total_ms"] for sample in samples)})
            all_samples.extend({"repeat": repeat, **sample} for sample in samples)

    metrics = summarize(cases)
    metrics.update({
        "mode": mode, "protocol": "2025-11-25", "sdk": version("mcp"),
        "environment": {"os": platform.system(), "architecture": platform.machine(),
                        "python": platform.python_version(), "sqlite": sqlite3.sqlite_version},
        "benchmark_concurrency": concurrency, "benchmark_runs": runs,
        "benchmark_calls_per_second": len(all_samples) / sum(run["seconds"] for run in runs),
        "benchmark_latency_ms": {
            metric: latency(sample[metric] for sample in all_samples)
            for metric in ("discovery_ms", "authorization_ms", "execution_ms", "total_ms")
        },
    })
    output.mkdir(parents=True, exist_ok=True)
    with (output / "scenario_comparison.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=cases[0], lineterminator="\n")
        writer.writeheader()
        writer.writerows(cases)
    timing_fields = ["repeat", "discovery_ms", "authorization_ms", "execution_ms", "total_ms"]
    with (output / "latency_samples.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=timing_fields, extrasaction="ignore",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(all_samples)
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (output / "metrics.prom").write_text(prometheus(metrics))
    print(f"{mode}: {metrics['scenario_passes']}/{len(cases)} scenarios, "
          f"{len(all_samples)} successful measured calls")
    if metrics["scenario_passes"] != len(cases):
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=MODES, default="quick")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(run(args.mode, args.output))
