# Executed verification — Project 06

Date: 2026-11-14 Asia/Kolkata. Synthetic local reference only. Python 3.11.14 / Linux aarch64 / SQLite 3.46.1 in Docker Desktop. Host Python 3.9.6 was deliberately not used for runtime verification.

| Check | Executed command / method | Outcome |
|---|---|---|
| Image and quick mode | `sh scripts/quickstart.sh` | PASS; 95 tests at this checkpoint and 64/64 quick scenario samples |
| Full mode | `sh scripts/full.sh` | PASS; 95 tests at this checkpoint, 960/960 expected outcomes, 7/7 labeled policy cases |
| Independent retained-artifact reconciliation | `python scripts/verify_artifacts.py results` in Python 3.11 image | PASS; population, quantiles, throughput, attempt/retry/duplicate/failure/recovery/wait counts and synthetic costs recomputed |
| Actual HTTP/restart smoke | `docker run --rm -v "$PWD:/lab" project06-agent-lab:local python scripts/verify_live.py` | PASS; live socket, pending approval, cross-tenant 404, independent approval, audit, metrics and persisted server restart |
| Installed package and CLI | Copy source to writable container /tmp; `pip install --no-deps /tmp/package`; unset PYTHONPATH; `agent-lab --mode quick --output /tmp/installed-output`; `pip check` | PASS; wheel built with pinned setuptools; 64/64 samples outside source tree; no broken requirements |
| Abrupt process death | `test_actual_process_death` | PASS; subprocess os._exit(77) after effect commit; exactly one simulated ticket after reopen/recovery |
| Non-idempotent crash / invalid write receipt | Dedicated tests | PASS; unknown state, no automatic replay; simulator ledger evidence reconciles |
| OTel instrumentation | `test_actual_otel_spans` with in-memory SDK exporter | PASS; workflow/tool spans share trace and correct parent; execution correlation verified. No live collector/export service tested |
| Dependency vulnerability audit | `python -m pip_audit -r /tmp/lab-requirements.txt --no-deps --disable-pip --format json` in existing verifier image | PASS; pip-audit 2.10.1, all 25 pinned packages, zero known findings, zero skipped packages |
| Dependency consistency | `pip check` in installed-package container | PASS |
| Formatting / unused imports | Ephemeral `ruff==0.14.5`, `ruff check --select F --fix src tests scripts`, `ruff format src tests scripts` | PASS at formatting checkpoint; subsequent small typed/config/report edits exercised by final tests |
| Secrets/privacy/staged diff | See repository security audit | Dedicated scanner and exact scope recorded there |
| Projects 01–05 | `git diff --name-only ed12c34 -- projects/0[1-5]*` | Empty; no earlier project files changed. Root index gains current project links |

Final source re-verification also restricts recovery control to the operator or execution owner and tests that a tenant-local reader cannot resume another owner's operator workflow. The original quick/full command checkpoints passed 95 tests before this additional security test; the final source suite passes 96.

Final automated population: **96 passed, 0 failed, 0 skipped**. Earlier runs exposed a JSON comment parsing error, corrected before all passing tests. The first wheel check used a read-only source mount; setuptools could not write egg-info. Repeating from a writable temporary copy passed. These initial failures were not concealed as successful checks. Initial SSH fetch failed host-key verification; an HTTPS fetch of the same public repository succeeded without remote configuration changes.

Full measured results: 49.12 scenario attempts/s, p50/p95/p99 active latency 6.729/20.135/43.723 ms; 43.75% business workflow success because failures/denials are intentionally injected; 100% expected-outcome match. Recovery: 120/120 samples. Sixty duplicate deliveries suppressed. Retry/replay amplification 1.1739. See benchmark_report.md for denominators, per-run variability and sample population. The API smoke and package installation shared the Docker host during part of the benchmark; resource isolation was not enforced.

Approval expiration uses a virtual clock; wait totals are simulated and excluded from measured active wall time. The full run observed 4,020 virtual approval-wait seconds across decisions and expiration. No human response-time performance is claimed. Simulated planning/tool charges total 4.14 arbitrary units; no provider calls or cloud charges occurred. Cost planning_calls_simulated counts admitted charged plans (900), not all pre-admission deterministic planner invocations.

Not executed / limitations: production authentication, external adapters, true network tool timeouts, multi-process/distributed workers, power/storage loss, real customer inputs, production-scale load, complete prompt-injection evaluation, live OTel collector, container OS vulnerability scan, cloud deployment, production SLO measurement. Local API is public-fixture identity only; release as an educational lab requires these limits to remain prominent. These optional deployment checks are not represented as passing.

Publication update: the owner authorized feature-branch publication on 2026-11-14 with “please publish.” Fresh final-source verification passed 96 tests and all retained artifact checks; fresh secret/privacy/dependency audits are recorded in the repository security audit. The authorized action is a normal feature-branch push only. Final commit and remote verification are returned in the publication delivery. This is an educational reference, not production-deployment readiness; main merge, tagged release and cloud deployment are outside this authorization.
