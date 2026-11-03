# Measured local benchmark — 3 November 2026 (IST)

Python 3.11.14, Darwin arm64, HTTPX in-process ASGI. Three measured runs per scenario, 80 requests/run, concurrency eight, no warmup. Source workloads, configuration and per-run values are in `benchmark.json`; all records are synthetic. No hostnames, usernames or personal filesystem paths are retained.

| Scenario | RPS mean ± sample SD | Mean run p50 ms | Mean run p95 ms | Mean run p99 ms | Successes | Run costs (micro-USD) |
|---|---|---|---|---|---|---|
| economy | 211.58 ± 7.50 | 33.06 | 55.30 | 61.68 | 240/240 | 2160, 2160, 2160 |
| quality | 161.94 ± 10.21 | 42.85 | 79.98 | 81.62 | 240/240 | 21600, 21600, 21600 |
| timeout_recovery | 187.82 ± 11.14 | 30.91 | 119.96 | 168.25 | 240/240 | 3969, 4077, 4293 |

Percentiles above are means of per-run nearest-rank percentiles, not pooled percentiles. Throughput includes all attempts, including any rejection. JSON records status/error/rejection rates, routes, retries, fallback, actual/estimated tokens, cost per success and final circuit state. Every run independently compares reported costs with settled SQLite charges. `scripts/validate_results.py` recomputes throughput, sample variability, token totals and per-model price arithmetic.

Configured provider sleeps are 5/10/5 ms; measured provider-attempt latency includes event-loop scheduling, timeout waits and failed attempts. Gateway overhead is the sum of gateway request elapsed time less provider-attempt elapsed time, divided by request count. It includes validation, SQLite, audits, retry backoff and scheduling; it is not a CPU measurement. End-to-end latency is client-observed ASGI time. Network, TLS, real tokenization, streaming and external providers are excluded. There is no production scalability claim.

Timeout recovery injects economy timeouts, restores normal behavior when request 40 is admitted, and records routing/circuit recovery. A circuit skips unhealthy work, so the failure workload can show higher throughput than healthy traffic under this local scheduling workload; that is not a reliability performance improvement. Benchmark prices are $1/$10/$2 per million synthetic tokens, different from the intentionally tiny demo prices. Healthy economy/quality requests use 27 actual versus 51 estimated tokens, so normal actual costs are 27 and 270 micro-USD respectively; fallback costs 54.

Earlier exploratory runs at a 30 ms provider timeout showed scheduling-induced healthy-provider timeouts during local contention. Defaults were revised to 75 ms/provider and a 300 ms request deadline; this report contains the rerun. Background desktop activity, synchronous SQLite transactions and filesystem latency remain confounders. Re-run on an otherwise idle host and inspect variability rather than extrapolating these results.

Each timeout workload now records its end-of-load circuit state, then waits 110 ms and measures a separate primary-only recovery probe. All three probes returned economy/HTTP 200 and closed the circuit. Probe latency and 27 micro-USD charge are reported separately and excluded from the 80-request load throughput, percentiles and cost totals. The complete ledger is checked against load charges plus probe charge. The standalone A–I drill also verifies half-open recovery.
