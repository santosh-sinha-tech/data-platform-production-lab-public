# Executed verification

**Reference Implementation · Synthetic / Illustrative workload**

Verified locally on **2026-09-16** using Docker, Airflow 3.3.1, Python 3.11, PySpark 3.5.7, and Java 17. This is evidence of the local experiment, not a production deployment or performance benchmark.

## Automated tests

Executed from the project directory:

```bash
docker compose build
docker compose run --rm lab python -m pytest -q
```

Observed result:

```text
22 passed in 52.52s
```

Coverage includes real Parquet generation, transformation, quality evaluation and routing for healthy and 82% deliveries; mandatory null violations; reconciliation FAIL and WARN; volume boundaries and empty delivery; changed data after validation; inconsistent publication decisions; idempotent routing; run reuse; interrupted storage copies; missing controls; missing columns; mixed currency; invalid contracts; and run-path validation.

Behaviour tests use 1,000 expected bookings for fast feedback. The separate Airflow experiments below use the full 100,000-record expectation.

## Full Airflow experiments

```bash
docker compose run --rm lab python -m booking_pipeline.cli healthy --run-id healthy-demo
docker compose run --rm lab python -m booking_pipeline.cli incomplete-source --run-id incomplete-demo
docker compose run --rm lab python scripts/verify_experiments.py
```

All commands exited with status 0. Both runs used the real four-task DAG through Airflow's synchronous `dag.test()` mode. All four tasks reported `success` in both runs. No task was skipped or marked successful artificially.

| Observed result | `healthy-demo` | `incomplete-demo` |
| --- | --- | --- |
| Orchestration | SUCCESS | SUCCESS |
| Transformation | SUCCESS | SUCCESS |
| Records expected | 100,000 | 100,000 |
| Records received | 100,000 | 82,000 |
| Completeness | 100% | 82% |
| Volume check | PASS | FAIL |
| Mandatory null check | PASS; 0% in every mandatory field | PASS; 0% in every mandatory field |
| Reconciliation | PASS | FAIL |
| Expected amount, USD | 54,891,100.00 | 54,891,100.00 |
| Processed amount, USD | 54,891,100.00 | 44,874,730.00 |
| Signed variance, USD | 0.00 | −10,016,370.00 |
| Absolute variance | 0% | 18.247712288513075% |
| Overall quality | PASS | FAIL |
| Publication | PUBLISHED | QUARANTINED |

The independent verifier read the persisted Parquet, validated row counts and SHA-256 fingerprints, checked the recorded Airflow task states, and confirmed no conflicting destination existed:

```text
VERIFIED healthy-demo: 100,000 rows, PASS, published; all four Airflow tasks succeeded
VERIFIED incomplete-demo: 82,000 rows, FAIL, quarantine; all four Airflow tasks succeeded
VERIFIED: incomplete-source run has no trusted published partition
```

Raw quality results are retained locally under `data/results/healthy-demo/` and `data/results/incomplete-demo/`. Generated data and runtime outputs are excluded from Git; this document contains the observed, non-sensitive summary. Repeating the commands requires fresh run IDs, as explained in the README.

## Release recheck — 2026-10-15

Repeated the documented Docker build, tests, both full-size scenarios, and persisted-output verifier in a clean clone of the reviewed implementation before the clean-history release copy. All commands exited with status 0. The tests reported **22 passed in 16.67s**. The healthy run published 100,000 records; the incomplete run quarantined 82,000 records. All four Airflow tasks succeeded in both runs, and the verifier confirmed that the incomplete run had no trusted published partition.

Both Mermaid diagrams rendered in the authenticated GitHub interface. Relative documentation links resolved. A redacted Gitleaks scan of the clone's reachable Git history reported no leaks. These checks are bounded verification evidence, not a guarantee against every possible security issue or a dependency vulnerability audit.

## Verification limits

This run verifies the local DAG and filesystem publication boundary. It does not test a continuously running scheduler, distributed Spark, cloud storage, multi-writer concurrency, or production identity controls.
