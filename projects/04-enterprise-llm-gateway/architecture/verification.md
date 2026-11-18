# Verification record

Executed 3 November 2026 (IST). Python 3.11.14 was built from official python.org source in temporary storage after the GitHub standalone runtime download timed out. All published paths below are repository-relative. No private build logs are committed.

```sh
# From projects/04-enterprise-llm-gateway, activated Python 3.11 environment
pip install -r requirements.txt
sh scripts/verify.sh
# 32 passed; all A–I drills PASS; report arithmetic PASS

# Fresh local Docker deployment
docker compose -p project04-gateway up -d --build
docker compose -p project04-gateway exec -T gateway python - < scripts/smoke.py
docker compose -p project04-gateway restart gateway
docker compose -p project04-gateway exec -T gateway python - < scripts/smoke.py
# Health, generation, durable replay, isolation, metrics and OpenAPI PASS
```

The container uses Python 3.11.14 slim pinned to manifest digest `sha256:c8271b1f627d0068857dce5b53e14a9558603b527e46f1f901722f935b786a39`, nonroot UID 65534 and persisted SQLite volume. Initial Docker daemon check failed because it was stopped; Docker Desktop was started, then build/startup/HTTP/restart checks were executed. An immediate post-start smoke attempt initially raced readiness; the runner now polls health for five seconds and passes. An earlier development-volume key also correctly returned 409 after the parsed default timeout changed (the full request fingerprint changed); the task-created volume was reset before the final fresh deployment check. Test resources are stopped and the dedicated verification volume removed after verification.

Dependency audit: pip-audit 2.10.1 against the complete 26-package pinned `requirements.txt`, including pip/setuptools, with `--no-deps --disable-pip`: zero known advisories and zero skips. This lock contains the fully resolved dependency closure, not only direct packages. No package hashes are included; package-index integrity and future advisory changes remain limits. Runtime/test dependencies are pinned; audit/formatting tools are external temporary tools.

Native Gitleaks 8.30.1 binary SHA256 was checked against official release metadata. Final staged snapshot and `origin/main..HEAD` history scans are recorded in the security audit. No scanner suppression is used. The README originally triggered curl-auth-header matches on public mock identities; curl examples now use a shell variable and pass the scanner.

Failures corrected during development: a venv unexpectedly used Python 3.9 and failed type-annotation collection; a repository-root test invocation collected unrelated projects without their environments; an isolation assertion incorrectly expected no beta audit record after a beta denial; a concurrent duplicate test's tight provider timeout allowed a legitimate replay-safe provider retry. The test now isolates idempotency using a long provider timeout, while retry behavior has dedicated tests. The short benchmark load could finish before breaker cooldown, so a separately reported and charged post-cooldown primary recovery probe was added; all three probes pass and remain outside load metrics. No prior project files were changed. Final checks run from Project 04 on Python 3.11; no tests are skipped.

See [benchmark report](../results/benchmark.md), [failure report](../results/failure-scenarios.md) and [security audit](../../../docs/security-audits/04-enterprise-llm-gateway.md). Sizing calculations are estimates; benchmark measurements are actual local simulator results. Proposed local latency SLOs are acceptance objectives, not measured production commitments.
