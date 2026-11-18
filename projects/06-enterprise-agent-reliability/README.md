# Project 06 — Enterprise AI Agent Reliability & Governance Lab

Can we trust an agent to execute the correct action safely? This working local reference puts deterministic controls between a simulated planner and six synthetic enterprise tools. Python 3.11, FastAPI, strict Pydantic contracts, durable SQLite state, approval gates, retries, reconciliation, audit records and Prometheus exposition run without credentials or paid services. Projects 01–05 are independent and unchanged.

## Execute

From this directory, one command builds the pinned Python 3.11 image, runs automated tests and executes quick mode:

```sh
sh scripts/quickstart.sh
```

Full experiments, benchmark and artifact arithmetic validation:

```sh
sh scripts/full.sh
```

Alternatively, with Python 3.11 installed:

```sh
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python -m pytest -q
PYTHONPATH=src .venv/bin/python -m agent_lab.experiments --mode full --output results
.venv/bin/python scripts/verify_artifacts.py results
```

The full pinned dependency closure is requirements.txt; pyproject.toml pins direct requirements. Quick runs 2×2×16=64 scenarios; full runs 3×20×16=960. Each uses fresh databases and an excluded warm-up. Results contain expected/actual outcomes and repeated-run variability, not invented target performance.

Start the optional local API with a persistent volume (one process/worker):

```sh
mkdir -p runtime
# Docker files are not authentication; bind this demo only to loopback.
docker run --rm --name project06-api -p 127.0.0.1:8006:8000 -v "$PWD/runtime:/lab/runtime" project06-agent-lab:local
```

In another terminal:

```sh
curl -s http://127.0.0.1:8006/executions -H 'Content-Type: application/json' -H 'X-Lab-Identity: alpha-operator' -d '{"key":"demo-deploy-1","workflow":"deploy"}'
# Copy the returned id into EXECUTION_ID, then approve as an independent fixture identity:
EXECUTION_ID=replace-with-returned-id
curl -s -X POST "http://127.0.0.1:8006/executions/$EXECUTION_ID/approve" -H 'X-Lab-Identity: alpha-approver'
curl -s "http://127.0.0.1:8006/executions/$EXECUTION_ID/audit" -H 'X-Lab-Identity: alpha-operator'
curl -s http://127.0.0.1:8006/metrics
```

Real loopback HTTP/restart smoke verification after building the image:

```sh
docker run --rm project06-agent-lab:local python scripts/verify_live.py
```

Interactive API schema: [local docs](http://127.0.0.1:8006/docs). Other POST actions are `reject`, `recover`, `reconcile`, `cancel`; GET execution/audit reads enforce tenant visibility. `alpha-reader` cannot write; `beta-approver` cannot see or approve alpha executions. Identity headers are public demo fixtures and can be impersonated; this server is unsuitable for public exposure. Custom actions and injected faults are intentional lab interfaces. Approval parameters have no mutation API. Tests tamper with stored plans to verify binding failure.

## Evidence and design

- [Architecture, locked 13-section structure](architecture/architecture.md)
- [Runbooks and SLOs](architecture/runbooks.md)
- [Verification procedure](architecture/verification.md)
- [Executed verification](results/verification_report.md)
- [Measured benchmark](results/benchmark_report.md), [metrics](results/metrics.json)
- [Scenario comparison](results/scenario_comparison.csv), [failure analysis](results/failure_analysis.md)
- [Repository security audit](../../docs/security-audits/06-enterprise-agent-reliability.md)

The simulated effect ledger and receipts do not establish exactly-once delivery to an external service. Process recovery is explicitly invoked through recover; there is no background scheduler. Approval expiration is evaluated by approve/recover, so operators must sweep pending work. Untrusted output remains inert text and is redacted before audit/output persistence; finite deterministic fixtures do not demonstrate complete prompt-injection resistance. The SQLite simulator stores synthetic raw effect content locally; never supply real sensitive data.

Stop the API with `docker stop project06-api`. Local state is under ignored runtime/. After stopping all processes, remove only this project's runtime databases to reset the lab. Reviewed summary results are committed; raw databases, environments and bulk logs are excluded. No cloud resources are created.
