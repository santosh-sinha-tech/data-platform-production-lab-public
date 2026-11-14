# Executed local simulated benchmark

Mode: full. 3 repeated runs using a fresh database for every scenario sample × 20 repetitions × 16 scenarios = 960 attempts; one excluded warm-up. Single serial worker; SQLite WAL; no HTTP network, model inference or external tool calls. Environment: `{"concurrency": 1, "machine": "aarch64", "os": "Linux", "python": "3.11.14", "sqlite": "3.46.1", "workers": 1}`. Database creation/checkpoint/close overhead is included in throughput wall time; workflow percentiles time submit/control operations after schema initialization. These populations differ intentionally.

- Throughput: 49.12 scenario attempts/s; between-run sample standard deviation 13.01.
- Active workflow latency p50/p95/p99: 0.006729/0.020135/0.043723 seconds. p95 between-run standard deviation 0.006296 seconds.
- Tool latency p50/p95/p99: 0.000572/0.002349/0.004815 seconds.
- Workflow success: 43.75%; includes deliberately denied/failed scenarios. Expected scenario outcomes: 960/960.
- Recovery success: 100.00% over 120 crash-replay/reconciliation samples.
- Retry amplification: 1.1739 attempts per attempted distinct step; 240.0 scheduled classified retries (including retries subsequently denied by budget). Crash replay included separately in amplification.
- Duplicate request suppression: 60; each duplicate test asserts the original execution ID and tests verify side-effect count.
- Policy accuracy: 100.00% on 7 hand-labeled finite cases; no claim of arbitrary-policy correctness.
- Approval waits: 4020 virtual seconds, excluded from wall-clock latency. This is a clock-driven expiration experiment, not measured human response time.
- Simulated planning/tool cost: 4.140000 units. No provider charges. Persistence and telemetry proxies described in architecture.

Infrastructure cost proxies: {"audit_cost_proxy": 0.00031644, "planning_calls_simulated": 900, "prices": {"audit_byte": 1e-09, "planning": 0.001, "state_write": 1e-06, "telemetry_event": 1e-07, "tool": 0.002}, "real_provider_calls": 0, "retry_and_replay_cost": 0.48, "state_cost_proxy": 0.0117, "state_writes_proxy": 11700, "telemetry_cost_proxy": 0.00037799999999999997}. Logical state mutations use the documented sizing proxy, not measured disk I/O. Audit bytes are payload-only and telemetry is counted events, not observed network traffic.

No production-scale, network, concurrent-worker, external exactly-once or prompt-injection-proof claim follows from these results. Durations vary with host scheduling, filesystem caching and virtualization. Decisions, counts and simulated cost reproduce; timestamps, execution IDs and latency do not.

Execution confounder: the API smoke and installed-package checks shared the Docker host during part of this benchmark. CPU/filesystem isolation was not enforced; run-to-run variation is retained, not normalized away.
