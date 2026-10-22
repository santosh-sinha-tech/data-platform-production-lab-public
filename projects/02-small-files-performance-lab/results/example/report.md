# Small Files Performance Lab — measured run

Run: `20261022T135633Z-7c3c6c90`; started UTC: 2026-10-22T13:56:33.778862+00:00

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
  "disk_free_before_cleanup_bytes": 313680818176,
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
    "spark.eventLog.dir": "file:///lab/runs/20261022T135633Z-7c3c6c90/events"
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
    }
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
    }
  }
}
```

Fragmented/compacted Parquet byte ratio: 1.059. Comparability warning (>25% difference): False.

Order-independent fingerprints match the generated source. Hash aggregates are probabilistic checks, not proof of multiset equality.

## Query results

| Query | Fragmented median s | Compacted median s | F/C ratio | Fragmented IQR s | Compacted IQR s |
|---|---:|---:|---:|---:|---:|
| full_aggregation | 0.252116 | 0.181126 | 1.392 | 0.079076 | 0.016807 |
| selective | 0.217320 | 0.148615 | 1.462 | 0.045484 | 0.018176 |
| partition_pruned | 0.139255 | 0.114690 | 1.214 | 0.026011 | 0.005076 |

Ratio >1 favors compaction; <1 favors fragmentation. See JSON/CSV for every sample and output checksum.

## Economics

Measured rewrite duration: 1.254179 s. Includes fragmented read, redistribution and write; excludes validation.

Each query is modeled as a separate future workload; do not add these break-even counts.

```json
{
  "full_aggregation": {
    "base": {
      "saved_seconds_per_read": 0.07098979099998814,
      "compaction_compute_cost": 0.0,
      "saved_compute_cost_per_read": 0.0,
      "break_even_reads": 18,
      "cost_break_even_reads": null,
      "rate_per_compute_hour": 0.0
    },
    "compaction_time_source": "measured",
    "sensitivity": [
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.03549489549999407,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 36,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.03549489549999407,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 36,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.03549489549999407,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 36,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.07098979099998814,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 18,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.07098979099998814,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 18,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.07098979099998814,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 18,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.10648468649998222,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 12,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.10648468649998222,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 12,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.10648468649998222,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 12,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      }
    ]
  },
  "selective": {
    "base": {
      "saved_seconds_per_read": 0.06870479100001603,
      "compaction_compute_cost": 0.0,
      "saved_compute_cost_per_read": 0.0,
      "break_even_reads": 19,
      "cost_break_even_reads": null,
      "rate_per_compute_hour": 0.0
    },
    "compaction_time_source": "measured",
    "sensitivity": [
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.034352395500008015,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 37,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.034352395500008015,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 37,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.034352395500008015,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 37,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.06870479100001603,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 19,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.06870479100001603,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 19,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.06870479100001603,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 19,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.10305718650002405,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 13,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.10305718650002405,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 13,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.10305718650002405,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 13,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      }
    ]
  },
  "partition_pruned": {
    "base": {
      "saved_seconds_per_read": 0.024564957999984927,
      "compaction_compute_cost": 0.0,
      "saved_compute_cost_per_read": 0.0,
      "break_even_reads": 52,
      "cost_break_even_reads": null,
      "rate_per_compute_hour": 0.0
    },
    "compaction_time_source": "measured",
    "sensitivity": [
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.012282478999992463,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 103,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.012282478999992463,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 103,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 0.5,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.012282478999992463,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 103,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.024564957999984927,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 52,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.024564957999984927,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 52,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.024564957999984927,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 52,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 0,
        "saved_seconds_per_read": 0.03684743699997739,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 35,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 1,
        "saved_seconds_per_read": 0.03684743699997739,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 35,
        "cost_break_even_reads": null,
        "rate_per_compute_hour": 0.0
      },
      {
        "savings_multiplier": 1.5,
        "rate_multiplier": 2,
        "saved_seconds_per_read": 0.03684743699997739,
        "compaction_compute_cost": 0.0,
        "saved_compute_cost_per_read": 0.0,
        "break_even_reads": 35,
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
  "successful_task_attempts": 336,
  "input_bytes": 21471568,
  "input_records": 2100000,
  "shuffle_read_bytes": 4026635,
  "shuffle_write_bytes": 4026635
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
