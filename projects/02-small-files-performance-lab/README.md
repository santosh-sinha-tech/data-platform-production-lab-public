# Small Files Performance Lab

**Project 02 · Synthetic / illustrative booking-event workload**

Identical records can read differently because file listing, footer reads, scan packing and scheduling depend on physical layout. This lab creates fragmented Snappy Parquet, rewrites it into larger files, verifies logical equivalence, and measures three identical query workloads. Compaction can improve, leave unchanged, or worsen elapsed time.

## Run with Docker

Requires Docker Engine/Desktop with Compose v2, network for the first build, 4 GiB container memory and about 2 GiB free disk for quick mode plus image space. No cloud accounts, credentials or external APIs. From this project directory:

```bash
docker compose build
docker compose run --rm lab bash scripts/run.sh
```

This runs pytest and quick mode together. Output appears in `runs/<UTC timestamp>-<random suffix>/`: report.md, report.json, samples.csv, config.json, plans/, events/, data/. New run directories prevent overwrites. Failure exits nonzero; initialized runs retain FAILED.json and partial data for diagnosis. Delete only the specific disposable run after inspection. No success report is written on failure.

```bash
# Benchmark only
docker compose run --rm lab python -m small_files.cli --config config/quick.json
# Larger workload: review disk/memory sizing first
docker compose run --rm lab python -m small_files.cli --config config/large.json
# Tests only
docker compose run --rm lab python -m pytest -q
```

Native alternative: Python 3.11, Java 17, `python -m venv .venv`, activate the environment, `pip install -r requirements.txt`, then `bash scripts/run.sh`. Docker copies the official versioned Apache Spark distribution and installs the small pinned Python dependencies; native setup obtains Spark through pip. Runtime versions and Python dependencies are pinned; Docker base images are pinned by digest, while OS package repositories remain mutable, so this is reproducible configuration, not a bit-identical image guarantee.

## Configure the experiment

Copy a JSON configuration and supply its path. `rows`, `seed`, `partitions` (logical bucket cardinality and generation parallelism), `fragmented_files`, `compacted_files`, `warmups`, `iterations`, `cores`, and `partitioned` control data and execution. In partitioned mode target counts must divide evenly across buckets. The controlled writer creates each bucket independently and repartitions within it; actual Parquet counts and file size distributions are always measured. No assertion assumes Spark honors an exact target. Unpartitioned mode omits the partition-pruning benchmark, retaining the same logical bucket column.

Events have an ID, UTC timestamp, synthetic customer ID, region, integer amount in cents, status and event_bucket. Partition buckets deliberately mix regions; pruning is on event_bucket=0. Hash-based generation is stable for a fixed configuration on the pinned Spark version. Changing bucket cardinality changes that field; changing execution partitioning of an existing frame does not change records.

Set `compute_hour_cost` to your estimated currency units per compute-hour. Default 0 makes no monetary claim. Optionally set `compaction_seconds` to a finite nonnegative supplied duration; the report retains measured rewrite duration and labels which input economics uses. There is no actual cloud billing integration. Each query has its own time and cost break-even model. Negative or zero savings have no break-even. Sensitivity scenarios are explicit assumptions.

## Read the evidence

[Example report](results/example/report.md) comes from an actual quick run. Its JSON/CSV and explain plans are retained beside it; datasets and raw event logs stay ignored. It is one machine/run, not a service performance promise. Read [verification](architecture/verification.md), [architecture](architecture/architecture.md), and [trade-offs](architecture/tradeoffs.md) before interpreting ratios.

Measured time covers relation construction, metadata listing, planning, execution and result collection. The aggregate forces amount column reads rather than metadata-only row counting. Full aggregation, selective customer/status filtering, and bucket pruning return small region aggregates. Every result is hashed after sorting by region, outside the measured interval. Both layouts use identical settings and query expressions. Warmups precede measured rounds and order alternates; no Spark persistence is used. These are warm filesystem tests: validation, prior writes, OS cache, JIT and fixed query order remain confounders. No statistical significance claim is made from five samples.

File lengths are measured on disk. Scan partition counts are labeled planning proxies. Spark event logs provide measured application-wide successful task counters, including writes/validation/warmups; they must not be attributed to an individual query. Explain statistics are never reported as runtime I/O or tasks. Output query `matched_records` differs from physical scan input records; the report also records full dataset row counts.

For deeper tuning, Apache's [Spark 3.5.8 performance documentation](https://spark.apache.org/docs/3.5.8/sql-performance-tuning.html) defines file open cost, scan packing, and adaptive execution. `openCostInBytes` is a planning estimate; `maxPartitionBytes` controls packing/splitting. Neither equals observed file-open latency. Several files can share a task and a large file can produce multiple splits. Filter pushdown, partition pruning, column pruning and shuffle aggregation all affect the outcome.
