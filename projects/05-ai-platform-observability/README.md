# Project 05 — Enterprise AI Platform Observability Lab

An HTTP 200 is only transport success. This executable local lab correlates latency, answer quality, retries, and simulated cost using request IDs and OpenTelemetry trace IDs. It runs independently of Projects 01–04. All facts, providers, tenants, and prices are synthetic. No cloud credentials or paid APIs.

## Run

Python **3.11** is required. From this directory, one command creates an environment, installs pinned dependencies, runs tests and executes quick mode:

```sh
sh scripts/quickstart.sh
```

Or use Docker (no local Python required):

```sh
docker compose build api
mkdir -p runtime
docker compose run --rm api python -m pytest
docker compose run --rm api python -m ai_observability.benchmark --mode quick --output /runtime/quick
docker compose run --rm api python -m ai_observability.benchmark --mode full --output /runtime/full
docker compose up -d
curl -s http://localhost:8000/query -H 'Content-Type: application/json' -H 'X-Lab-Key: demo-a' -d '{"scenario":"unsupported"}'
curl -s http://localhost:8000/metrics
curl -s http://localhost:8000/records -H 'X-Lab-Key: demo-a'
```

For installed local Python:

```sh
PYTHONPATH=src .venv/bin/python -m ai_observability.benchmark --mode full --output results
PYTHONPATH=src .venv/bin/uvicorn ai_observability.app:app --host 127.0.0.1 --port 8000 --no-access-log
```

API: localhost:8000/docs. Prometheus: localhost:9090. Grafana: localhost:3000; its initial local admin login must be changed on first use. These services bind to loopback. Demo identity headers are public local fixtures, not secrets or production authentication. Never expose this stack publicly.

`POST /query` accepts bounded tenant/application profiles and a configured scenario. `POST /stream` emits two synthetic NDJSON tokens and measures scheduled first emission. `GET /records` returns only the demo identity's tenant records. Metrics and health are operator surfaces, not tenant APIs. A single-process fixed-minute tenant quota defaults to 120 requests/minute in the live server (`LAB_TENANT_RPM`). Benchmark app instances use 10,000 to avoid interference. `ai_rate_limit_rejections_total / ai_admission_attempts_total` measures rejections among authenticated valid attempts. A unit integration check exercises HTTP 429; benchmark traffic has no rejections. No circuit breaker is implemented.

## Evidence

- [Executed full benchmark](results/benchmark_report.md), [quick mode](results/quick/benchmark_report.md)
- [Machine-readable metrics](results/metrics.json), [scenario comparison](results/scenario_comparison.csv)
- [SLO budgets](results/slo_report.md), [failure analysis and runbooks](results/failure_analysis.md)
- [Simulated cost attribution](results/cost_analysis.csv), [verification](results/verification_report.md)
- Open `results/dashboard.html` in a browser for seven local measured views. This is generated directly from the workload, not a mockup.
- `results/traces-run-*.json` includes one trace per scenario per run, with request correlations in metrics.json. All spans are within one process; this is not a demonstration of cross-service distributed execution.
- Grafana provisions live rate/latency/quality/cost panels from actual API metrics. Generate traffic against the running API; benchmark ASGI process metrics are separate and do not magically populate the live server. Reports retain the benchmark snapshots. Each per-run Prometheus snapshot includes that run’s one warm-up request; benchmark summary and SLO populations exclude warm-up.
- [Architecture and operational contracts](architecture/architecture.md)

## Quality and reproducibility

`config/quality.json` is a hand-authored synthetic corpus with explicit reference facts and independently specified candidate claims/evidence. The evaluator does exact structured fact checks against these references, not lexical similarity or a factual oracle for arbitrary prose. Wrong answers, unsupported facts, bad citations, missing evidence, contradictions, stale evidence and appropriate abstention are separate cases. `metrics.json` reports all eight offline evaluations and signal-specific rates. Absent claims in appropriate abstention pass groundedness/citation vacuously; these rates include abstentions and are not citation precision among only cited claims. Appropriate abstention is separately denominated over cases labeled should_abstain.

All successful benchmark requests are evaluated for lab ground truth. A separate deterministic modulo-five online sampling simulation selects from these records; it is explicitly not a representative production sampling estimate. Prompt text is accepted only to test redaction and does not drive model decisions. Reference-label correctness is available only for this finite fixture corpus.

Quick: two independent runs × ten scenarios × four requests. Full: three × ten × thirty. Concurrency four, one excluded warm-up per run, fixed seeds 500+run, and scenario order baseline→incident→recovery. Decisions and simulated costs reproduce exactly; wall-clock times and UUID/trace IDs vary. Percentiles use nearest rank. Raw export files and SQLite live under ignored runtime/; only reviewed summaries and compact trace examples are committed.

Artifact arithmetic can be rechecked with `python scripts/verify_artifacts.py`. For a running Compose stack, run the real HTTP smoke check from the same network:

```sh
docker compose run --rm -v "$PWD:/lab" api python scripts/verify_live.py --stack
```

Optional `LAB_API_PORT`, `LAB_PROMETHEUS_PORT`, and `LAB_GRAFANA_PORT` override loopback host ports. Stack verification used 18005/19005/13005 to avoid other projects. Prometheus storage is ephemeral across container removal; export evidence before teardown.

Stop optional stack with `docker compose down`. Local SQLite/JSONL retention is manual: stop the API and remove only this project's runtime files when no longer needed. Prometheus retention is seven days. No cloud resources are provisioned.
