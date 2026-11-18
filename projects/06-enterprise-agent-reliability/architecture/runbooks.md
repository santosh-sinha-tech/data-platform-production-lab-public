# SLO definitions and runbooks

These are proposed 30-day rolling objectives for a future authenticated deployment. Local injected experiments validate controls and cannot establish production SLO compliance. Each ratio must retain counts, not average ratios across unequal populations.

| Objective | Target | Numerator / denominator | Exclusions and measurement |
|---|---|---|---|
| Workflow completion | ≥99% | Successful eligible workflows within 60 active seconds / admitted eligible terminal workflows | Exclude deliberate fault experiments, policy denials, explicit cancellations, approval wait. Track approval-dependent workflows separately; include stuck past-deadline workflows as failures. |
| Tool reliability | ≥99.5% | Valid successful tool attempts / all eligible tool attempts | Include retries in denominator; exclude intentional fault injection only. Durable step attempts and step_failure events. Unknown counts as failure until reconciled; never silently erase the original failure. |
| Duplicate side-effect prevention | 100% objective | Duplicate deliveries causing zero additional effects / all duplicate deliveries | Local request/step key evidence; external service ledger needed in production. Any breach pages immediately, even with tiny sample. |
| Recovery time | ≥99% within 60 s | Interrupted eligible workflows recovered/reconciled within 60 s from detection / all detected interrupted workflows | Approval-blocked work is tracked separately; missing evidence counts as unmet recovery. Lab has no background detection, so measure operator-triggered recovery separately. |
| Approval processing | ≥95% within 15 min | Valid approval requests granted/rejected within 15 min / all approval requests reaching 15 min age | Expiration and unanswered requests fail objective. Exclude cancelled-before-review requests and report counts. Human wait is separate from active tool latency. |

No production window has been observed. The benchmark recovery success metric has no recovery-time target and approval wait is virtual, so neither should be represented as an SLO pass. Duplicate suppression counts are not proof for arbitrary external adapters.

## Stuck workflows

1. Inspect tenant-authorized GET execution and audit; record execution/step IDs and last checkpoint. Never edit the database while a worker runs.
2. Check deadline, pending approval and unknown states. Stop additional workers; this lab supports one process only.
3. POST recover for running checkpoints. It reauthorizes and resumes idempotent work; non-idempotent executing steps become unknown. If deadline expired, inspect prior effects and create a new reviewed request only after reconciliation.
4. For unknown writes use the reconciliation procedure. Do not issue a new idempotency key to bypass uncertainty.

## Approval backlog

1. Inspect pending_approval rows/last approval_requested events in an operator-controlled database session. Production needs a tenant-scoped queue and approval-age dashboard.
2. Confirm independent approver tenant, action digest and expiry. Approve/reject using the exact execution endpoint.
3. POST recover to evaluate expired approvals. The lab has no timer scheduler; without this sweep rows can remain pending past expiry.
4. Never extend expiry or change the plan to reuse approval. Create a fresh reviewed workflow after resolving prior effects.

## Tool outage

1. Inspect failed attempt types, retry events and tool_latency histogram. A simulated timeout is not a real socket timeout measurement.
2. Stop new tool traffic outside the lab, then confirm per-workflow retry caps/deadline/cost. There is no implemented global circuit breaker.
3. Retry only adapters whose declared contract is both retry-safe and idempotent. Unknown non-idempotent completion requires evidence.
4. Resume checkpoints after authorization and observe recovery counts; do not replay completed steps.

## Duplicate execution alert

1. Preserve execution IDs, request hashes, step keys and redacted audit; compare effects by tenant and step key.
2. Stop additional workers and block affected writes. Do not delete idempotency records.
3. Determine whether duplicate delivery was suppressed, a key was changed, or an external adapter lacks a deduplication boundary.
4. Reconcile external effects and apply only explicitly reversible, authorized compensation. Open an incident for any actual duplicate side effect; do not claim success from HTTP status alone.

## Recovery after process restart

1. Restart a single process using the same runtime volume. Verify SQLite is readable; preserve database and WAL together if taking a copy while stopped.
2. Enumerate nonterminal records in an operator database session; for each known tenant POST recover. There is no automatic startup sweep.
3. Inspect executing idempotent steps for safe replay; unknown writes require trusted completion lookup. POST reconcile only when simulator ledger has evidence; missing evidence returns conflict.
4. Check effects, step receipts and audit. Restore from backups after storage failure requires a separately tested procedure, outside this lab.

## Suspected unauthorized action

1. Isolate the loopback demo and preserve audit/effects. Fixture headers provide no real authentication; never expose this API publicly.
2. Check tenant, persisted owner role, current policy, exact action digest and independent approval identity before inspecting effects.
3. Revoke access in a real identity system, not by editing workflow ownership; production entitlement lookup is required.
4. Reconcile and compensate only reversible authorized actions. Keep private evidence out of public Git; the repository security policy governs disclosure and publication.
