# Runbooks

## Budget or quota rejection

Check authenticated `/v1/usage` for charged and reserved amounts in the configured period. Unresolved holds count against budget. Confirm tenant and application policy rather than raising limits reflexively. 402 is budget, 429 rate/concurrency; honor Retry-After. A duplicate cached request does not consume quota again. Do not rotate idempotency keys to hide uncertain execution.

## Provider outage or open circuit

Inspect `gateway_events_total` provider error and circuit transition series. Compare `/metrics` latency by stage. Change the local YAML behavior to normal and restart for manual demonstrations, or use the test recovery scenario to observe half-open recovery without restart. No more than two attempts per candidate; quality routes cannot fallback to basic. Distinguish provider 429 from gateway 429. Fallback raises simulated spend when the replacement profile is more expensive.

## Unresolved accounting and restart

Stop the gateway and back up the DB. On restart reserved becomes unresolved; check usage before admitting more traffic. Preserve the key. Obtain external usage/completion evidence (for this pure simulator the operator can establish no external bill). Never infer zero cost from a timeout alone. Reconcile offline:

```sh
PYTHONPATH=src python scripts/reconcile.py --db gateway.db --tenant alpha --app chat --key affected-key --charge 0 --evidence synthetic-case-001
```

Charge must be nonnegative and no greater than held amount; contract violations require investigation. Evidence reference must contain no private data. Reconciled keys remain terminal. A future real adapter needs an outbox and provider-status reconciliation protocol. Crash tests seed a durable reserved row and recreate the app; they verify recovery state, not an OS power-loss durability experiment.

## Sensitive telemetry or database exposure

Stop affected logging/export paths, preserve access evidence privately, restrict DB/backups, rotate real credentials if later introduced, and follow repository SECURITY.md. Do not print prompt bodies, private evidence or scanner findings into public reports. `/metrics` is operator-only in a real deployment; bind this demo to localhost.

## Reproduce failures

Set each model `behavior` to normal, slow, timeout, 429, 500, intermittent, unavailable, missing_usage or incorrect_usage in a copied config and start with `GATEWAY_CONFIG=path/to/config.yaml`. A configured profile can also set `available: false` or `timeout: 0.075`. Tests exercise every mode. `sh scripts/verify.sh` writes measured benchmark JSON. `PYTHONPATH=src python scripts/scenarios.py` writes the named A–I report.
