# Failure injection results

Executed on Python 3.11.14 with synthetic profiles and temporary SQLite state. All nine named scenarios passed their assertions; `failure-scenarios.json` contains actual bounded outcomes. The test suite additionally covers every configured failure mode, missing/incorrect usage, unsafe-adapter timeout, cancellation holds, half-open probe exclusion and stale breaker completions.

| Scenario | Executed outcome |
|---|---|
| A Normal routing | Economy, HTTP 200 |
| B Budget exhaustion | HTTP 402 after one permitted simulated charge |
| C RPM rejection | HTTP 429, Retry-After 60 |
| D Timeout fallback | Two bounded primary attempts, fallback success |
| E Circuit recovery | Open → half-open → closed; primary restored |
| F Same-budget race | 20 requests; 3 successes, 17 budget denials; 3 micro-USD charged |
| G Duplicate key | One provider invocation and one ledger record |
| H Isolation | Beta denied quality model; no beta ledger record from alpha traffic |
| I Unsettled restart | Reserved row becomes unresolved; one micro-USD remains held |

Restart drill recreates the exclusive app over seeded durable reservation state; it is not a kill/power-loss test. Separately, the Docker HTTP check verifies completed replay after an actual container restart. Propagated task cancellation is tested; ordinary HTTP disconnect may allow processing and settlement to continue. Invalid usage is not retried: it retains an unresolved hold. Real provider exactly-once execution is outside this simulator's guarantees.
