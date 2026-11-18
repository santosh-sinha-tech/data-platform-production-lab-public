# Release verification — Project 05

Executed 2026-11-10 (Asia/Kolkata). Synthetic, single-process provider experiment; no paid resources, commercial LLMs or cross-service provider tracing.

## Runtime and results

Standalone Docker image built from digest-pinned Python 3.11.14-slim and 25 exact pinned Python dependencies. Benchmark environment: {"cpus": 10, "memory_bytes": 8218034176, "arch": "aarch64", "docker": "28.3.2"}. Resources describe the Docker engine, not dedicated benchmark reservations. Other local containers and shared host scheduling can affect measurements. No hostname, personal path or private mailbox is retained.

- Final Python 3.11 suite: **33 passed, 0 failed, 0 skipped**.
- Quick: 80 measured requests in two runs, one excluded warm-up/run.
- Full: 900 measured requests in three runs, 30 requests/scenario/run, concurrency four, seeds 500–502.
- Full measured throughput: 68.204 requests/s.
- ASGI round-trip p50/p95/p99: 31.016/108.844/114.528 ms.
- Application lifecycle p50/p95/p99: 21.057/100.135/105.644 ms.
- HTTP 200: 765/900; quality failures among HTTP 200: 225/765 (29.412%).
- Provider attempts: 1530; additional primary retries: 540; fallback requests: 90; attempts/request: 1.7.
- Simulated input/output tokens: 414000/22950; total simulated cost: $0.503100. Additional-attempt cost $0.117000, including fallback-attempt cost $0.057600 (overlapping views, do not add).
- Total platform cost / HTTP-successful request = $0.00065765, including failed-request waste.
- Eight offline quality fixtures: 2 pass all criteria, 6 intentionally fail. Exact reference correctness 87.5%, groundedness 37.5%, citation support 25%, abstention-decision agreement 50%. Appropriate abstention among should-abstain cases: 1/5=20%. These are properties of an intentionally adversarial fixture set, not real-world model quality.
- Synthetic online sample: 153 successful selected records, 45 quality failures. Deterministic modulo-five selection can be biased.

## SLO outcome

All scenarios, including deliberately broken traffic, are included. Budget consumption factors above one mean exhaustion.

| Objective | Good / eligible | SLI | Target | Budget consumed |
|---|---:|---:|---:|---:|
| availability | 765/900 | 85.0000% | 99% | 15.000× |
| latency | 607/900 | 67.4444% | 95% | 6.511× |
| quality | 540/765 | 70.5882% | 95% | 5.882× |
| cost | 810/900 | 90.0000% | 99% | 10.000× |

Synthetic paired-window burn alerts trigger during the generated incident and clear after generated recovery. This is arithmetic validation on equal-weight events, not production alert validation. Healthy recovery does not erase consumed historical workload budgets.

## Executed commands

From the project directory (the final verification mounted current source onto the standalone built image):

```sh
docker compose -p project05 build api
docker run --rm -v "$PWD:/lab" -w /lab project05-api:latest python -m pytest
docker run --rm -v "$PWD:/lab" -w /lab project05-api:latest python -m ai_observability.benchmark --mode quick --output results/quick
docker run --rm -v "$PWD:/lab" -w /lab project05-api:latest python -m ai_observability.benchmark --mode full --output results
docker run --rm -v "$PWD:/lab" -w /lab project05-api:latest python scripts/verify_artifacts.py
LAB_API_PORT=18005 LAB_PROMETHEUS_PORT=19005 LAB_GRAFANA_PORT=13005 docker compose -p project05 up -d
docker run --rm --network project05_default -v "$PWD:/lab" -v "$PWD/runtime:/runtime" -w /lab project05-api:latest python scripts/verify_live.py --stack
```

Equivalent repository-root executions used `-f projects/05-ai-platform-observability/docker-compose.yml` and corresponding relative bind paths. Benchmark run IDs and timings vary; reports are from actual execution.

## Verification scope

- All ten configured failure scenarios executed in both workload modes and over actual HTTP to the separately running API.
- W3C context, span parent links, stage timing/status, metric counts, percentile method, cost attribution, quality fixtures, SLO denominators/budgets, burn thresholds/window boundaries, queue delay, tenant isolation, persistence, redaction, deterministic decisions and report generation covered by tests.
- Artifact verifier reconciled scenario counts/costs, all attribution dimensions, exported span parents and trace correlations for quick/full runs.
- Docker Compose syntax/build/startup and API health passed. The final Docker build permission review initially timed out; its narrower retry succeeded. Prometheus target health and stored generated request count passed; Grafana database health passed. Dashboard provisioning is checked separately in the audit evidence. No screenshot is presented as measurement.
- Dependency audit: pip-audit 2.10.1 direct pinned audit (`--no-deps --disable-pip -r requirements.txt --format json`): 25 packages, zero known vulnerabilities, zero skips. Resolver-based preliminary audit also passed but returned 24 packages; direct audit closes that coverage difference. Package versions are pinned but wheel hashes are not locked.
- Dedicated Gitleaks v8.30.1 staged-tree scan and ten-commit main-to-implementation history scan passed with zero leaks; privacy and unrelated-project checks passed. Exact implementation SHA is `ed96d3559d556bc46595d30453113b97d4e5e799`. The audit-record follow-up is separately scanned. Scope and tool digest are recorded in [the repository audit report](../../../docs/security-audits/05-ai-platform-observability.md). The owner subsequently authorized feature-branch publication after fresh security checks; see the audit publication record. No main merge is authorized.

## Failures, skips and limits

- Local system Python was 3.9, so Python 3.11 validation ran in Docker. Host-only quickstart was not executed. Docker standalone build and equivalent commands were executed.
- Initial container dependency setup had an incorrect bind path and failed before installing anything; corrected mount and isolated lock generation passed. No results from that failed setup are included.
- Initial Git whitespace review detected CSV CRLF endings; the writer was fixed to LF and artifacts normalized without changing values. Subsequent whitespace and artifact checks passed.
- Live verifier initially raced Prometheus’s first scrape after restart; a bounded 20-second polling window fixed the check, and the complete stack check was rerun.
- Sandboxed Docker access initially failed; authorized Docker access succeeded. SSH fetch failed host-key verification; public main was refreshed over HTTPS without changing the configured remote.
- OS/container CVE scans, real provider billing/tokenization, commercial-model quality, cloud deployment, production auth, hostile multi-tenant deployment and multi-process load were not tested.
- Local Grafana/Prometheus versions and base image are digest-pinned for repeatability, not certified current or free of OS/image vulnerabilities. Keep loopback-only and review/upgrade before shared hosting.
- A single-process fixed-minute tenant rate limiter is implemented and tested with HTTP 429; no circuit breaker, production retention automation, alert delivery or automatic quality gate exists. SQLite is a local single-writer store. Trace files are local and require manual retention cleanup; memory buffer is bounded at 10,000 spans.
- Local reference implementation readiness: ready for review/reproduction. Production readiness: no. The owner authorized public feature-branch publication following fresh tree/history/privacy/dependency checks and final-range verification. Production deployment remains outside this authorization.
