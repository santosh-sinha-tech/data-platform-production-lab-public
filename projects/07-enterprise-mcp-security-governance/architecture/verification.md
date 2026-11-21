# Verification method

Use the README commands from the project root. The suite checks actual MCP initialization, tool listing, protocol calls, registry consistency, approval binding, tenant identity, credential scope, response projection, duplicate effects, audit redaction and latency formulas. Every labeled scenario runs twice in pytest with isolated databases and compares its stable security outcomes.

The quick run uses two independent series across A–N and two batches of 40 measured calls at concurrency one. The full run uses three independent series across A–N and three batches of 300 measured calls at concurrency four. Benchmarks use an initialized session and perform discovery, validation, SQLite audit writes and tool RPC for each request. End-to-end request timing excludes subprocess startup and teardown. Wall-clock throughput includes batching and request handling inside each run.

Nearest-rank quantiles are calculated over pooled samples. Per-run total latency ranges and call rates show variation. Scenario denial rate uses the labeled synthetic case mix. Drift rate measures the two seeded change types. Prevention rate uses B–J and L. Audit completeness checks required fields for each primary attempt. Approval wait uses a deterministic fixture clock and represents approval age at dispatch. It does not measure human review speed.

Verify CSV/JSON counts, outcomes, recovery, and throughput arithmetic with `scripts/verify_results.py`. Repeat runs produce new timestamps and correlation IDs. Security outcomes and expected effect counts are deterministic.
