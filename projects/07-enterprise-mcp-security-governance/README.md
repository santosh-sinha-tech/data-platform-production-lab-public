# Project 07 — Enterprise MCP Security & Governance Lab

The gateway decides whether a discovered tool may execute. The official MCP SDK initializes a local stdio session, lists tools, and calls an approved tool. Registry trust, tenant access, credential scope, approval, output projection, and audit evidence are gateway policies.

## Run the lab

From this project directory, using Python 3.11 or later:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q
.venv/bin/python scripts/run.py --mode quick --output /tmp/mcp-lab-quick
.venv/bin/python scripts/run.py --mode full --output /tmp/mcp-lab-full
.venv/bin/python scripts/verify_results.py /tmp/mcp-lab-full
```

The SDK is pinned to **1.30.0** and the gateway requires the negotiated **2025-11-25** revision. The SDK supplies `ClientSession` and the low-level `Server`. See the [SDK source at the pinned tag](https://github.com/modelcontextprotocol/python-sdk/tree/v1.30.0) and the [MCP specification at the pinned revision](https://modelcontextprotocol.io/specification/2025-11-25).

The benchmark writes to the specified directory and uses ephemeral SQLite databases. It requires no network or credentials after installation. It runs against a local Python API with fixture identities. Approvals are issued by a separate reviewer fixture through that API. The scenario runner stands in for the human review interaction.

| Location | Contents |
| --- | --- |
| `config/policy.json` | Registry, role grants, target ownership, reviewed tool definitions |
| `src/mcp_governance/` | Gateway, protocol adapter, SQLite store, scenario and metrics logic |
| `servers/` | Synthetic MCP operations server and failure fixtures |
| `tests/` and `scripts/` | Assertions, experiment runner and evidence verifier |
| `architecture/` | Design review, security model, runbooks and verification method |
| `results/` | Executed full-run evidence, findings, benchmark and verification reports |

The fixture server models reads as a fixed operational state and writes as durable synthetic receipts. The lab uses a single host trust boundary. It exercises control decisions with synthetic identities, data and credential claims.
