# Reproducible verification procedure

1. From the project root run `sh scripts/quickstart.sh`; it builds the pinned Python 3.11 image, runs pytest, and executes 64 quick scenario samples.
2. Run `sh scripts/full.sh` for 960 samples, 3 repeated runs, all 16 scenarios, a 7-case labeled policy evaluation, then independent artifact arithmetic checks.
3. Inspect results/scenario_comparison.csv; every expected outcome must match. Inspect metrics.json for run sample sizes, machine/Python/SQLite and variability. Do not compare raw success rate with scenario correctness.
4. Run the loopback API commands in README; the ASGI integration test exercises API approval, cross-tenant rejection, audit and metrics. HTTPX uses an in-process transport, so it does not verify a live socket. Run `docker run --rm project06-agent-lab:local python scripts/verify_live.py` for actual loopback HTTP and persisted server restart; report its outcome separately.
5. Test crash safety: pytest runs a separate Python process, commits a simulated effect, exits abruptly with code 77, then reopens the same SQLite file. It verifies one effect and successful idempotent recovery. The uncertain write scenario verifies no retry and trusted ledger reconciliation.
6. Inspect prohibited action, revoked policy on retry/resume, approval digest/expiry and strict input tests. Malicious output is retained as inert text with sensitive token redaction; no tool escalation is allowed.
7. Review exact staged diff, unchanged Projects 01–05, privacy, excluded runtime files, pinned dependencies and commit identity. Run required dedicated scanner and vulnerability audit; record failures/skips. Never treat pattern search as a dedicated scanner.
8. Review results/verification_report.md and repository security audit before release. Local commit is authorized; push, merge and publication require explicit approval and a fresh full unpublished-range audit.

Deterministic reproducibility applies to scenario outcomes, effects, attempts and synthetic cost. Wall-clock latency, execution IDs, trace IDs and timestamps vary. Approval time is virtual and benchmark latency excludes virtual human delay. The benchmark directly calls the engine, serially; concurrent HTTP throughput and distributed recovery are unmeasured.
