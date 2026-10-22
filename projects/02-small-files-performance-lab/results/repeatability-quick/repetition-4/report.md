# Small Files Performance Lab — measured run

Run: `20261022T140643Z-a38cd39a`; started UTC: 2026-10-22T14:06:43.271121+00:00

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
  "disk_free_before_cleanup_bytes": 313613086720,
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
    "spark.eventLog.dir": "file:///lab/runs/repeatability/20261022T140545675015Z/repetition-4/20261022T140643Z-a38cd39a/events"
  },
  "cgroup_memory_max": "4294967296",
  "cgroup_cpu_max": "200000 100000"
}
```

## Layouts and validation

```json
{
  "fragmented": {
    "files": 48,
    "parquet_bytes": 1587154,
    "min_file_bytes": 33006,
    "median_file_bytes": 33063.5,
    "max_file_bytes": 33141,
    "all_file_bytes": 1600050,
    "fingerprint": {
      "rows": 60000,
      "amount_cents": 29937654953,
      "hash_sum_1": "-1949383388043342745731",
      "hash_sum_2": "-1339046577505984934202"
    },
    "schema": "struct<event_id:bigint,event_timestamp:timestamp,customer_id:bigint,region:string,amount_cents:bigint,status:string,event_bucket:int>",
    "bucket_rows": {
      "2": 15000,
      "0": 15000,
      "1": 15000,
      "3": 15000
    },
    "partition_directories": [
      "event_bucket=0",
      "event_bucket=1",
      "event_bucket=2",
      "event_bucket=3"
    ]
  },
  "compacted": {
    "files": 4,
    "parquet_bytes": 1498500,
    "min_file_bytes": 374519,
    "median_file_bytes": 374587.5,
    "max_file_bytes": 374806,
    "all_file_bytes": 1510280,
    "fingerprint": {
      "rows": 60000,
      "amount_cents": 29937654953,
      "hash_sum_1": "-1949383388043342745731",
      "hash_sum_2": "-1339046577505984934202"
    },
    "schema": "struct<event_id:bigint,event_timestamp:timestamp,customer_id:bigint,region:string,amount_cents:bigint,status:string,event_bucket:int>",
    "bucket_rows": {
      "2": 15000,
      "1": 15000,
      "0": 15000,
      "3": 15000
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

Fragmented/compacted Parquet byte ratio: 1.059. Comparability warning (>25% difference): False.

Order-independent fingerprints match the generated source. Hash aggregates are probabilistic checks, not proof of multiset equality.

## Query results

| Query | Fragmented median s | Compacted median s | F/C ratio | Fragmented IQR s | Compacted IQR s |
|---|---:|---:|---:|---:|---:|
| full_aggregation | 0.262690 | 0.161582 | 1.626 | 0.051531 | 0.021868 |
| selective | 0.225148 | 0.137673 | 1.635 | 0.015261 | 0.011030 |
| partition_pruned | 0.131366 | 0.114735 | 1.145 | 0.016769 | 0.005718 |

Ratio >1 favors compaction; <1 favors fragmentation. See JSON/CSV for every sample and output checksum.

## Economics

Measured rewrite duration: 1.403127 s. Includes fragmented read, redistribution and write; excludes validation.

This is processing-time amortization of one rewrite, not cloud financial payback. Each query is modeled as a separate future workload; do not add these break-even counts. Infrastructure pricing, billing granularity, object-store requests, idle capacity and recurring compaction costs are excluded.

```json
{
  "full_aggregation": {
    "base": {
      "saved_seconds_per_read": 0.1011077080000149,
      "compaction_compute_cost": 0.0,
      "saved_compute_cost_per_read": 0.0,
      "break_even_reads": 14,
      "cost_break_even_reads": null,
      "rate_per_compute_hour": 0.0
    },
    "compaction_time_source": "measured",
    "sensitivity": [
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.05055385400000745,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 28,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.05055385400000745,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 28,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.05055385400000745,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 28,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.1011077080000149,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 14,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.1011077080000149,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 14,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.1011077080000149,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 14,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.15166156200002234,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 10,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.15166156200002234,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 10,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.15166156200002234,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 10,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      }
    ]
  },
  "selective": {
    "base": {
      "saved_seconds_per_read": 0.08747516700000801,
      "compaction_compute_cost": 0.0,
      "saved_compute_cost_per_read": 0.0,
      "break_even_reads": 17,
      "cost_break_even_reads": null,
      "rate_per_compute_hour": 0.0
    },
    "compaction_time_source": "measured",
    "sensitivity": [
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.04373758350000401,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 33,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.04373758350000401,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 33,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.04373758350000401,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 33,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.08747516700000801,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 17,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.08747516700000801,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 17,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.08747516700000801,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 17,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.13121275050001202,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 11,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.13121275050001202,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 11,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.13121275050001202,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 11,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      }
    ]
  },
  "partition_pruned": {
    "base": {
      "saved_seconds_per_read": 0.016631250000003206,
      "compaction_compute_cost": 0.0,
      "saved_compute_cost_per_read": 0.0,
      "break_even_reads": 85,
      "cost_break_even_reads": null,
      "rate_per_compute_hour": 0.0
    },
    "compaction_time_source": "measured",
    "sensitivity": [
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.008315625000001603,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 169,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.008315625000001603,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 169,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.008315625000001603,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 169,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.016631250000003206,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 85,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.016631250000003206,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 85,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.016631250000003206,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 85,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.02494687500000481,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 57,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.02494687500000481,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 57,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.02494687500000481,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 57,
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
  "successful_task_attempts": 352,
  "input_bytes": 21628264,
  "input_records": 2220000,
  "shuffle_read_bytes": 4027136,
  "shuffle_write_bytes": 4027136
}
```

## Configuration

```json
{
  "rows": 60000,
  "seed": 42,
  "partitions": 4,
  "fragmented_files": 48,
  "compacted_files": 4,
  "warmups": 1,
  "iterations": 5,
  "cores": 2,
  "partitioned": true,
  "compute_hour_cost": 0.0,
  "compaction_seconds": null
}
```

Local results do not predict cloud object-store request latency, throttling, egress, cluster startup or actual billing. Repeat larger runs on the deployment storage before choosing compaction policy.
