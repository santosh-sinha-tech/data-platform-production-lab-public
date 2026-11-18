# Project 04 — Enterprise LLM Gateway

Executable local reference for cost, reliability and governance. All inputs and provider results are synthetic. No paid API, cloud account or secret is required. **Local mock authentication is not production identity management.** Release status and the owner-authorized public feature-branch publication are recorded in the security audit.

## Run

From this directory, using Python 3.11:

```sh
python3.11 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
sh scripts/start.sh
```

Or one-command container startup: `docker compose up --build`. It binds localhost and persists SQLite in a named volume. Run one worker and one replica only. Stop the old process before restarting; startup recovery assumes exclusive ownership of the database.

Open `http://127.0.0.1:8000/docs` for generated OpenAPI. Verification: `sh scripts/verify.sh` after environment setup. This runs tests and three measured repetitions of each benchmark workload.

```sh
DEMO_KEY=demo-alpha
curl -s http://127.0.0.1:8000/v1/generate \
  -H 'Content-Type: application/json' -H "X-API-Key: $DEMO_KEY" \
  -H 'Idempotency-Key: demo-001' \
  -d '{"app":"chat","prompt":"hello","input_tokens":5,"max_output_tokens":16}'
curl -s -H "X-API-Key: $DEMO_KEY" http://127.0.0.1:8000/v1/usage
curl -s -H "X-API-Key: $DEMO_KEY" http://127.0.0.1:8000/v1/audit
curl -s http://127.0.0.1:8000/metrics
```

`demo-alpha` and `demo-beta` are intentionally public demonstration identities. Alpha permits chat/batch and all models; beta permits chat/economy only. Idempotency keys are scoped by authenticated tenant and application. Request IDs accept an optional valid UUID in `X-Request-ID` (otherwise a UUID is generated), returned in headers and response metadata; successful replays retain the original response ID while the HTTP header identifies the replay attempt.

## API and policies

`POST /v1/generate` accepts app, prompt, capability (basic/quality), optional model, input_tokens, max_output_tokens (1–1024), timeout (0.01–2 seconds), cost_ceiling (integer micro-USD), and allow_fallback. Input has a configurable `limits.input_chars` bound with a hard ceiling of 4096 characters and 16384 estimated tokens. The synthetic tokenizer counts UTF-8 bytes; estimates below that deterministic minimum are denied. Provider output is capped at eight simulated tokens. These units are illustrative, not any vendor tokenizer.

Routing: explicit model or basic→economy / quality→quality. Check app authorization, model allowlist, capability, configured availability and per-request estimated cost ceiling. Reserve the maximum cost of permitted candidate routes. Attempt primary if its breaker admits traffic, then fallback if enabled, permitted and capability-compatible. Quality requests never downgrade to the basic fallback. A named model is not an authorization bypass. No route gives 403. Future adapters must encode residency constraints; these local profiles have no residency guarantees.

Budgets are integer micro-USD (`1 USD = 1,000,000 micro-USD`), both tenant and per-application. `price` is micro-USD per million total tokens: example 100 means $0.0001/million synthetic tokens. Deliberately small prices keep local arithmetic visible. Change configuration for meaningful price comparisons. `GET /v1/costs` reports tenant/application/model attribution, held funds, utilization and fallback cost deltas. Request cost is rounded up once to a micro-USD. The named accounting period `2026-11` is fixed until an operator changes it; it does not silently roll over with wall time. Keep old periods for audit; unresolved liabilities require investigation before rollover.

Reservation, idempotency claim, minute quotas and concurrent admission share a SQLite `BEGIN IMMEDIATE` transaction. Settlement replaces the hold with the actual charge; unused reservation is released. Fixed-minute tenant RPM/TPM use conservative estimated tokens with no refunds; concurrency is tenant-wide. 429 has Retry-After (60 seconds for minute quotas; one second for concurrency). Boundary bursts are possible. Budget denial is 402; unauthenticated is 401; policy denial 403; conflicting/pending/terminal keys 409; validation 422; provider exhaustion/unknown completion 503. Errors contain only a code and request ID.

Provider attempts have a 75 ms timeout, two attempts maximum per model and 1 ms bounded backoff. Circuit opens after two failures, cools for 100 ms, admits one half-open probe, then closes on success or reopens on failure. Total dispatch deadline is request.timeout; database/HTTP scheduling overhead can extend wall latency. Retry/fallback on timeout is safe only because the simulated adapter is pure and replay-safe. This is not a safe default for billable vendor APIs.

Successful responses are durably cached. In-flight duplicates return 409; completed duplicates return the cached result without dispatch or charge. Failures are terminal for their key; use a new key for a deliberate new request. Missing/invalid usage and cancellation after dispatch become unresolved and retain budget. On exclusive restart all reserved records become unresolved. A real provider completion and SQLite settlement are not one transaction: exactly-once external execution is not guaranteed. Operator reconciliation never redispatches the old key.

## Layout and evidence

- `src/gateway/`: API/policy coordination, durable store, provider/breaker interfaces.
- `config/example.yaml`: synthetic identities, budgets, profiles, failure modes.
- `tests/`: adversarial policy, concurrency, recovery, failure and reporting checks.
- `scripts/`: startup, verification, benchmark and offline reconciliation.
- `results/`: reviewed measured evidence; runtime DB/log files are excluded.
- `architecture/`: review, verification, trade-offs and runbooks.

[Architecture review](architecture/architecture.md) · [Verification](architecture/verification.md) · [Runbooks](architecture/runbooks.md) · [Trade-offs](architecture/tradeoffs.md).
