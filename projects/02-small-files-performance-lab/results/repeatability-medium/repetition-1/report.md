# Small Files Performance Lab — measured run

Run: `20261022T140742Z-566049fe`; started UTC: 2026-10-22T14:07:42.541744+00:00

Synthetic data. Warm filesystem/JVM experiment; no guaranteed performance improvement.

## Environment

```json
{
  "spark_version": "3.5.8",
  "python": "3.11.11 (main, Apr  8 2025, 09:48:09) [GCC 12.2.0]",
  "java": "17.0.20.1",
  "platform": "Linux-6.10.14-linuxkit-aarch64-with-glibc2.36",
  "machine": "aarch64",
  "visible_cpu_count": 10,
  "local_cores": 2,
  "physical_memory_bytes": 8218034176,
  "disk_free_before_cleanup_bytes": 312890716160,
  "spark_settings": {
    "spark.sql.session.timeZone": "UTC",
    "spark.sql.adaptive.enabled": "false",
    "spark.sql.shuffle.partitions": "4",
    "spark.sql.parquet.compression.codec": "snappy",
    "spark.sql.files.maxPartitionBytes": "134217728",
    "spark.sql.files.openCostInBytes": "4194304",
    "spark.sql.parquet.filterPushdown": "true",
    "spark.sql.parquet.enableVectorizedReader": "true",
    "spark.sql.parquet.aggregatePushdown": "false",
    "spark.eventLog.enabled": "true",
    "spark.eventLog.compress": "false",
    "spark.ui.enabled": "false",
    "spark.driver.memory": "1g",
    "spark.eventLog.dir": "file:///lab/runs/repeatability/20261022T140742262195Z/repetition-1/20261022T140742Z-566049fe/events"
  },
  "cgroup_memory_max": "4294967296",
  "cgroup_cpu_max": "200000 100000"
}
```

## Layouts and validation

```json
{
  "fragmented": {
    "files": 256,
    "parquet_bytes": 311016365,
    "min_file_bytes": 1214270,
    "median_file_bytes": 1214896.5,
    "max_file_bytes": 1215507,
    "all_file_bytes": 313448769,
    "fingerprint": {
      "rows": 12000000,
      "amount_cents": 5998770732672,
      "hash_sum_1": "13354645358635102201832",
      "hash_sum_2": "13462783092494031043388"
    },
    "schema": "struct<event_id:bigint,event_timestamp:timestamp,customer_id:bigint,region:string,amount_cents:bigint,status:string,event_bucket:int>",
    "bucket_rows": {
      "2": 3000000,
      "1": 3000000,
      "3": 3000000,
      "0": 3000000
    },
    "partition_directories": [
      "event_bucket=0",
      "event_bucket=1",
      "event_bucket=2",
      "event_bucket=3"
    ]
  },
  "compacted": {
    "files": 16,
    "parquet_bytes": 293014730,
    "min_file_bytes": 18312130,
    "median_file_bytes": 18313718.0,
    "max_file_bytes": 18314361,
    "all_file_bytes": 295304098,
    "fingerprint": {
      "rows": 12000000,
      "amount_cents": 5998770732672,
      "hash_sum_1": "13354645358635102201832",
      "hash_sum_2": "13462783092494031043388"
    },
    "schema": "struct<event_id:bigint,event_timestamp:timestamp,customer_id:bigint,region:string,amount_cents:bigint,status:string,event_bucket:int>",
    "bucket_rows": {
      "2": 3000000,
      "3": 3000000,
      "1": 3000000,
      "0": 3000000
    },
    "partition_directories": [
      "event_bucket=0",
      "event_bucket=1",
      "event_bucket=2",
      "event_bucket=3"
    ]
  }
}
```

Fragmented/compacted Parquet byte ratio: 1.061. Comparability warning (>25% difference): False.

Order-independent fingerprints match the generated source. Hash aggregates are probabilistic checks, not proof of multiset equality.

## Query results

| Query | Fragmented median s | Compacted median s | F/C ratio | Fragmented IQR s | Compacted IQR s |
|---|---:|---:|---:|---:|---:|
| full_aggregation | 1.130572 | 0.711435 | 1.589 | 0.086241 | 0.008453 |
| selective | 0.937171 | 0.499460 | 1.876 | 0.073078 | 0.025224 |
| partition_pruned | 0.372838 | 0.238487 | 1.563 | 0.005595 | 0.042581 |

Ratio >1 favors compaction; <1 favors fragmentation. See JSON/CSV for every sample and output checksum.

## Economics

Measured rewrite duration: 14.781750 s. Includes fragmented read, redistribution and write; excludes validation.

This is processing-time amortization of one rewrite, not cloud financial payback. Each query is modeled as a separate future workload; do not add these break-even counts. Infrastructure pricing, billing granularity, object-store requests, idle capacity and recurring compaction costs are excluded.

```json
{
  "full_aggregation": {
    "base": {
      "saved_seconds_per_read": 0.4191367499999785,
      "compaction_compute_cost": 0.0,
      "saved_compute_cost_per_read": 0.0,
      "break_even_reads": 36,
      "cost_break_even_reads": null,
      "rate_per_compute_hour": 0.0
    },
    "compaction_time_source": "measured",
    "sensitivity": [
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.20956837499998926,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 71,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.20956837499998926,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 71,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.20956837499998926,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 71,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.4191367499999785,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 36,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.4191367499999785,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 36,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.4191367499999785,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 36,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.6287051249999678,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 24,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.6287051249999678,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 24,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.6287051249999678,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 24,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      }
    ]
  },
  "selective": {
    "base": {
      "saved_seconds_per_read": 0.4377112919999604,
      "compaction_compute_cost": 0.0,
      "saved_compute_cost_per_read": 0.0,
      "break_even_reads": 34,
      "cost_break_even_reads": null,
      "rate_per_compute_hour": 0.0
    },
    "compaction_time_source": "measured",
    "sensitivity": [
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.2188556459999802,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 68,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.2188556459999802,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 68,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.2188556459999802,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 68,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.4377112919999604,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 34,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.4377112919999604,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 34,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.4377112919999604,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 34,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.6565669379999406,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 23,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.6565669379999406,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 23,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.6565669379999406,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 23,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      }
    ]
  },
  "partition_pruned": {
    "base": {
      "saved_seconds_per_read": 0.13435108299998433,
      "compaction_compute_cost": 0.0,
      "saved_compute_cost_per_read": 0.0,
      "break_even_reads": 111,
      "cost_break_even_reads": null,
      "rate_per_compute_hour": 0.0
    },
    "compaction_time_source": "measured",
    "sensitivity": [
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.06717554149999216,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 221,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.06717554149999216,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 221,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.06717554149999216,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 221,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.13435108299998433,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 111,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.13435108299998433,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 111,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.13435108299998433,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 111,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.2015266244999765,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 74,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.2015266244999765,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 74,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.2015266244999765,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 74,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      }
    ]
  }
}
```

A zero hourly rate means no monetary conclusion. Time break-even still applies. Sensitivity varies observed savings by 0.5/1/1.5 and rate by 0/1/2 of supplied rate; these are scenarios, not confidence intervals.

## Measurement boundaries

Wall time includes relation creation, file listing, planning, execution and collection of small aggregates. No Spark cache/persist is used. Validation and warmups warm OS caches. Layout order alternates each round; query order is fixed. Single application, no cache eviction or cold-storage claim. JVM JIT, host contention, compression differences, tiny-data overhead and Docker virtualization remain confounders.

Parquet file bytes are filesystem lengths, not runtime scan bytes. Scan RDD partition counts in JSON are planning proxies, not measured tasks. Explain plans are post-action plans. Event metrics below are application-wide measured task counters and include validation/writes; they cannot attribute query savings.

```json
{
  "scope": "whole application including generation, validation, warmups, measured reads",
  "successful_task_attempts": 791,
  "input_bytes": 3830824364,
  "input_records": 498000000,
  "shuffle_read_bytes": 816132657,
  "shuffle_write_bytes": 816132657
}
```

## Configuration

```json
{
  "rows": 12000000,
  "seed": 42,
  "partitions": 4,
  "fragmented_files": 256,
  "compacted_files": 16,
  "warmups": 2,
  "iterations": 5,
  "cores": 2,
  "partitioned": true,
  "compute_hour_cost": 0.0,
  "compaction_seconds": null
}
```

Local results do not predict cloud object-store request latency, throttling, egress, cluster startup or actual billing. Repeat larger runs on the deployment storage before choosing compaction policy.
