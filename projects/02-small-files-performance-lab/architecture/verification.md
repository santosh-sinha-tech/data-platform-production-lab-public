# Verification protocol

Run `docker compose build` then `docker compose run --rm lab bash scripts/run.sh`. The runner executes unit and Spark integration tests before creating a new benchmark run. The Docker quick run itself is the smoke test (Python 3.11 + Java + Spark + filesystem mounts + reports).

Tests cover deterministic generation, seed changes, order-independent equivalence, row loss, partitioned and unpartitioned rewrites, physical file statistics, all query checksums, missing data, invalid configuration/results, median/IQR calculations, event metrics parsing and break-even/no-saving/zero-rate behavior.

The benchmark independently verifies both layouts against the generated source, validates every warmup/measured query result checksum across iterations and layouts, and rejects missing data, mismatched row counts, non-distinct physical layouts and nonpositive/nonfinite samples. Check report.json only after successful process exit. Inspect FAILED.json and raw Spark logs for failures. Tests are not an assurance of cloud production behavior.

Committed evidence lives in results/example/ with the exact config, report, samples and explain plans. Raw event logs/datasets remain in ignored runs/. See results/verification.md for executed checks, environment and limitations. Recreate records and checksums with the committed config; timings vary. Byte counts include actual Parquet lengths and a separately labeled all-file total including sidecars/markers. Input dataset rows and query matched records are distinct from application-wide Spark input-record counters.

## Pre-publication checks

Run `python -m small_files.repeatability --config config/quick.json --repeats 5` in the container for five independent Python/JVM applications, then repeat with config/medium.json. The analyzer rejects inconsistent configs, settings, runtime/resource limits, fingerprints, schemas, bucket rows/directories, query checksums or normalized plan structures. See results/publication-review.md for the completed quick and medium validation, variability and interpretation.
