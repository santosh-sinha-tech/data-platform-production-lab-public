# Release verification — Project 02

Verified on 22 October 2026. Synthetic workload; local Docker execution only.

## Checks executed

- Final digest-pinned Docker Compose build: PASS.
- Release command `docker compose run --rm lab bash scripts/run.sh`: PASS (exit 0).
- pytest: **27 passed in 13.13 seconds** on Python 3.11.11 / Spark 3.5.8.
- Docker smoke: PASS; the same container generated data, validated equivalence, executed queries and wrote all reports.
- Report cross-check: PASS; 36 CSV records = 3 queries × 2 layouts × (1 warmup + 5 measured), matching medians/checksums, six explain plans. CSV line endings normalized to LF for Git; parsed records unchanged. The writer now emits LF directly (format-only post-run change outside timed execution).
- Project 01 tracked diff: empty. Git whitespace check: PASS.

## Evidence and environment

Selected release run: `20261022T135633Z-7c3c6c90`, started 2026-10-22T13:56:33.778862+00:00.

Host: Apple Silicon Mac16,1, 10 CPUs, 16 GiB physical RAM. Docker Engine 28.3.2 Linux VM: 10 visible CPUs and 8,218,034,176 bytes RAM. Compose limit: 2 CPUs (`cpu.max=200000 100000`) and 4 GiB (`memory.max=4294967296`). Spark local[2], 1 GiB driver heap, Java 17.0.20.1, Linux aarch64, Python 3.11.11, Spark 3.5.8. Effective Spark settings and filesystem capacity are recorded in the example JSON. No intentional concurrent build ran during the release benchmark. Host activity and thermal/cache state are not controlled.

Both layouts contain 60,000 rows with equal cents totals and both independent hash sums. Fragmented: 48 files / 1587154 Parquet bytes. Compacted: 4 files / 1498500 bytes. Byte ratio: 1.0592. No >25% byte-comparability warning.

| Query | Fragmented median s (IQR) | Compacted median s (IQR) | F/C | Time break-even future reads |
|---|---:|---:|---:|---:|
| full_aggregation | 0.252116 (0.079076) | 0.181126 (0.016807) | 1.392 | 18 |
| selective | 0.217320 (0.045484) | 0.148615 (0.018176) | 1.462 | 19 |
| partition_pruned | 0.139255 (0.026011) | 0.114690 (0.005076) | 1.214 | 52 |

Measured rewrite: 1.254179 seconds. Cost rate is 0 (unsupplied), so no monetary payback claim. Break-even uses per-query median savings and equal compute capacity; treat small absolute savings and these five-sample ratios cautiously.

## Reproduce

From the repository root:

```bash
cd projects/02-small-files-performance-lab
docker compose build
docker compose run --rm lab bash scripts/run.sh
# Larger run (not executed for this release):
docker compose run --rm lab python -m small_files.cli --config config/large.json
```

## Build recovery and earlier checks

Initial pip-based builds encountered Debian HTTP delay, PyPI read timeouts, and finally a truncated PySpark archive (6.9 MB of 317.8 MB) rejected by its SHA-256 check. No integrity checks were bypassed. The final Dockerfile uses HTTPS Debian sources and the official digest-pinned Apache Spark distribution as a build stage, plus a digest-pinned Python base; its build and end-to-end execution passed. OS apt packages remain repository-resolved, with actual Java version recorded. Python requirements include the resolved pytest dependencies.

A supplemental existing-image preflight on Spark 3.5.7 passed 27 tests and completed a quick run. The first Spark 3.5.8 check passed 27 tests and a quick run, but overlapped with the final image rebuild. This example is the subsequent release run after that build; it was selected for the finalized environment, not by speed. Prior generated run directories remain ignored locally. The release run retains every measured sample, including outliers.

## Limitations and unexecuted checks

The 5-million-row configuration was not executed. Native host execution was not run because the host lacks Java and Python 3.11. No cold-cache trials, independent-application repetitions, cloud/object-store tests, monetary rate scenario benchmark or distributed cluster validation were executed. Nonzero rates and no-saving cases are unit-tested. Unpartitioned data/query behavior is Spark integration-tested; a full unpartitioned performance run was not executed.

Runtime event counters are application-wide, not per-query. Raw logs and datasets remain under ignored runs/; the committed event-log manifest identifies local raw logs, while report JSON includes parsed counters. Hash-sum equivalence is probabilistic. Local warm-cache behavior, small data, fixed query order, JIT, Docker virtualization, row ordering/compression and host contention limit inference. Cloud compaction policy requires representative distributed workload and billing analysis.

## Subsequent pre-publication review

The original checks above are historical. [Repeatability and scale review](publication-review.md) adds five independent quick applications, five medium applications (~293–311 MB/layout), full scan-metadata audits and an expanded 37-test suite. Use that review for the current evidence and cost-model limitations.
