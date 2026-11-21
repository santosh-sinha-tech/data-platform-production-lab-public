# Executed benchmark

Host environment was Darwin arm64 with Python 3.13.3, SQLite 3.49.1, MCP SDK 1.30.0 and protocol revision 2025-11-25. All requests used the real MCP stdio session, a local synthetic read and durable SQLite audit writes. One request-time tool listing was included per call. Subprocess startup and teardown were outside request latency and warm throughput. This was a shared general-purpose host run.

| Run | Repetitions × calls | Concurrency | Pooled calls/s | End-to-end p50 / p95 / p99 (ms) |
| --- | ---: | ---: | ---: | ---: |
| Quick | 2 × 40 | 1 | 244.91 | 3.79 / 5.10 / 9.68 |
| Full | 3 × 300 | 4 | 453.57 | 7.14 / 9.32 / 11.60 |

| Full component | p50 (ms) | p95 (ms) | p99 (ms) |
| --- | ---: | ---: | ---: |
| Live discovery | 3.00 | 4.38 | 5.25 |
| Initial authorization and input validation | 0.055 | 0.121 | 0.145 |
| Tool RPC and result projection | 2.86 | 3.87 | 5.25 |
| End to end | 7.14 | 9.32 | 11.60 |

Full-run throughput ranged from 430.55 to 472.54 calls/s. Its per-run p95 ranged from 8.28 to 9.71 ms. Quick throughput ranged from 236.78 to 253.61 calls/s. The two modes use different concurrency settings and run lengths. The timed authorization stage ends before discovery, durable reservation and approval validation. End-to-end timing includes those applicable gateway costs.

The full run had three primary scenario dispatches with a valid approval. Fixture approval age was 1,000 ms for each. This comes from an injected clock with no real reviewer wait. Scenario measurements and audit results are in [metrics](metrics.json), [scenario comparisons](scenario_comparison.csv) and [timing samples](latency_samples.csv).

Throughput is successful calls divided by wall-clock time summed across equally sized runs. Quantiles use nearest rank over the pooled samples. The artifact verifier recalculates quantiles, rates, scenario outcomes and throughput. The local measurements characterize the synthetic read workload and do not estimate remote service capacity.

## Local resource observation

In a separate native quick repeat, Python `resource.getrusage` recorded 0.712 s user CPU and 0.399 s system CPU for the runner. Waited-for subprocesses used 10.117 s user CPU and 1.705 s system CPU in aggregate. Reported maximum RSS was 62,324,736 bytes for the runner and 61,423,616 bytes in the child accounting scope. Child RSS is not concurrent aggregate memory. The resource observation includes fixture startup, injected failures and teardown. It measures neither energy nor price.
