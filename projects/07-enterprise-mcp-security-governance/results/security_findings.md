# Executed security findings

All 14 fixtures matched their expected decisions and effect counts in all three full-run repetitions. The effect column is the total per case, including setup and recovery. See [case-level evidence](scenario_comparison.csv).

| Case | Observed outcome | Effects per trial | Evidence |
| --- | --- | ---: | --- |
| A | `ok` | 0 | Approved read used real MCP discovery and execution |
| B | `unapproved_server` | 0 | Registry denied the pending server before connection |
| C | `unauthorized_tool` | 0 | Reader could not dispatch a pipeline rerun |
| D | `tenant_mismatch` | 0 | Alpha reader could not access the beta target |
| E | `definition_drift` | 0 | Changed input schema blocked an approved rerun |
| F | `definition_drift` | 0 | Changed description blocked a read |
| G | `quarantined` | 0 | Untrusted reply suppressed. Follow-on configuration write denied |
| H | `credential_audience` | 0 | Wrong-audience fixture grant rejected before dispatch |
| I | `approval_expired` | 0 | Expired approval produced no effect |
| J | `approval_replay` | 1 | First request succeeded. Replay produced no second effect |
| K | `timeout` | 0 | Slow read timed out. A fresh healthy session recovered |
| L | `duplicate` | 1 | Fresh approval could not repeat the same intent |
| M | `server_unavailable` | 0 | Subprocess exited before completing MCP initialization |
| N | `unknown` | 1 | Effect committed without reply. Repeat intent remained blocked |

The full run detected all six seeded definition changes and met all 30 prevention expectations across the selected ten fixture types. The gateway denied 27 of 42 primary case attempts under the experiment's policy-denial definition. All 42 primary attempts contained the required audit fields. These rates describe the fixture mix.

Additional tests verify that a cross-tenant reviewer cannot approve an action, changing exact arguments invalidates a grant, an unexpected server version is rejected, and two gateway instances sharing the store cannot both reserve the same intent. See [security model and residual risks](../architecture/security.md).
