# Trade-offs and boundaries

This reference supports one active gateway per SQLite database. Atomic SQL admission is exercised from multiple threads but does not establish safe multi-replica startup/recovery. Circuit and metrics state remain local. SQL calls are synchronous and can stall the event loop; use a bounded worker/async storage adapter before scaling.

Idempotency is durable without expiry, scoped by tenant/app/key and the complete request fingerprint. Even changes to timeout are conflicts. Cached response bodies live in SQLite. Retention must delete keys only after an explicitly agreed replay window; quotas and audit tables also need retention. Unknown records hold budget indefinitely pending evidence; do not auto-release a potentially billable completion. Offline reconciliation marks terminal reconciled, never fabricates a provider answer.

The fixed named accounting period is operator controlled; quotas use fixed wall-clock minutes and can burst at boundaries or be affected by clock changes. TPM counts reservations and retries do not debit additional quota, because failed pure simulations do not produce billable tokens. A real adapter must reserve and account every billable attempt, including failures and fallback. This implementation must not be connected to a paid provider without that change.

Synthetic token units are UTF-8 bytes, not a vendor tokenizer. Simulated charges are illustrative and rounded, never actual cloud bills. Local benchmarks use HTTPX ASGI, exclude network/TLS and do not establish production scalability. Raw prompt text is not stored, but cached synthetic response text and request hashes are. The no-op Screening extension does not provide PII detection, content moderation or enterprise DLP.
