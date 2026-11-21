# Operational runbooks

| Signal | First action | Evidence before resuming |
| --- | --- | --- |
| Definition drift or server version rejection | Pause affected tool in the registry and compare reviewed and advertised definitions in a safe viewer | Reviewed launch and definition snapshot, explicit new approval for high-impact calls |
| Tenant or credential mismatch | Check principal derivation, target ownership and issuance rules | Re-run cross-tenant and mismatched audience fixtures |
| Untrusted result | Preserve redacted correlation and isolate the affected server if needed | Investigate via a restricted channel and restore only reviewed tool output |
| Expired or replayed approval | Find the original request and any dispatch receipt | Issue a new grant only after checking the exact intended action and prior outcome |
| Unknown or in-flight write | Freeze that business intent and check downstream effects | Reconcile the existing receipt with a reviewer before authorizing further action |
| Read timeout or startup failure | Inspect process health and check configured version and capacity budget | Verify a healthy read on a fresh MCP session |
| Audit persistence failure | Stop the gateway and validate SQLite availability | Reconcile dispatch records and operations with missing terminal records |

Audit correlation identifies the attempt. The stable business intent identifies the write across attempts. In this lab, inspect the separate synthetic effects ledger to verify whether a write occurred. A production downstream service needs a durable lookup by business intent.
