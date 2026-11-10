# Security and privacy audit — Project 05: AI Platform Observability

## Scope and release identity

- Review date/time: 2026-11-10, Asia/Kolkata.
- Reviewer: Codex engineering review, local execution.
- Project: `projects/05-ai-platform-observability/`.
- Destination: public repository `santosh-sinha-tech/data-platform-production-lab-public`; no publication performed.
- Branch: `feat/05-ai-platform-observability`; intended comparison: `origin/main`.
- Verified main base: `8dfbd27fb9b18ea08d1cf863c85bdd43db30140e`, refreshed over public HTTPS. Existing SSH remote retained; SSH fetch failed host-key verification.
- Implementation parent: `1f7f882cd687b2087ca04795b2938feb659ff936`.
- Inherited commits ahead of main: nine, covering prior Projects 02–04 and policy records. They are included in the final history scan; this project's change diff is against its implementation parent.
- Exact implementation SHA and final scanned head: recorded in the post-commit evidence below. A report cannot contain its own SHA; the final audited report commit is identified by Git and the delivery report.
- Staged/final tree scope: entire index snapshot, including inherited tracked files; ignored runtime data, caches and environments excluded. No historical full-repository scan is implied by a main-to-head range scan.

## Executed checks

| Check | Command / method | Tool identity | Outcome |
|---|---|---|---|
| Staged scope, diff, whitespace | `git diff --cached --name-status`; `git diff --cached --check`; review exact index diff | Git 2.50.1 | PASS; 55 changed files in approved scope; no whitespace errors |
| Dedicated staged-tree scanner | `git checkout-index --all --prefix=TEMP/`; Docker Gitleaks `dir /scan --redact --no-banner` | Gitleaks v8.30.1; `ghcr.io/gitleaks/gitleaks@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f` | PASS, exit 0, zero leaks; final index tree 92f61981669bda03fbf09c11ed3a8cc5f88b8a13; native absent, Docker route executed |
| Full unpublished comparison range | Docker Gitleaks `git /repo --log-opts=origin/main..HEAD --redact --no-banner` | Same immutable image | PASS, exit 0, zero leaks; ten commits through ed96d3559d556bc46595d30453113b97d4e5e799, including nine inherited commits |
| Privacy / credentials / artifacts | Review personal paths, mailbox/phone/account/internal URL categories and complete staged diff; no raw sensitive findings copied | Manual + Python pattern review + Gitleaks | PASS; no unintended private metadata or runtime artifacts found |
| Synthetic provenance | Hand-authored structured synthetic facts, candidate answers, tenants, model profiles and tariffs | Source/config review | PASS; no copied customer or external datasets |
| Commit identity | `git log --format` plus configured author/committer review | Git 2.50.1 | PASS for inherited range; owner public identity and GitHub noreply mailbox |
| Dependency vulnerability review | `pip-audit --no-deps --disable-pip -r requirements.txt --format json` | pip-audit 2.10.1 | PASS, 25 pinned packages, zero known vulnerabilities, zero skips |
| Tests and measured evidence | Standalone Python 3.11 Docker; pytest; quick/full; artifact verifier; live HTTP | Python 3.11.14; pytest 9.2.0; Docker 28.3.2 | PASS: 33 tests, 80 quick requests, 900 full requests; arithmetic/correlation checks pass |
| Optional monitoring stack | Compose syntax/build/startup; Prometheus target/query; Grafana health and provisioning logs | Digest-pinned images in Compose | PASS; actual generated API request metrics scraped; Grafana dashboard provisioning finished without logged errors |
| Unrelated projects | Review index names and diff against implementation parent | Git | PASS; zero Project 01–04 diff against implementation parent |

## Findings and remediation

- No real AI/customer records or credentials are required. Demo keys are deliberately public local identities and provide no production authentication assurance.
- Safe logs contain only generated request ID, trace ID and HTTP status. Span attributes are allowlisted; prompts, answer bodies, documents, credential headers and exception text are excluded. SQLite records omit payload content.
- Tenant record API filters identity server-side and uses parameterized SQL. Aggregate metrics, local trace files and Grafana are operator-only boundaries; loopback binding is implemented, fine-grained production authorization is not.
- Metric labels are fixed route/stage/status/failure/model enums. Tenant IDs and request/trace IDs occur only in reviewed synthetic detail evidence, not metric labels.
- Runtime SQLite/JSONL, environments, caches and raw dependency-audit output are excluded. Reviewed summaries, a compact synthetic live smoke result and selected trace examples are intentionally retained.
- Dependencies have exact versions, no wheel hashes. Python base, Prometheus and Grafana image digests are pinned. Image/OS CVE and license-compliance automation were not run; dependency audit does not cover OS packages.
- Principal dependencies are established public upstream packages. Fixtures are authored locally. Grafana is an unmodified upstream AGPL distribution reference; no Grafana code is copied into this repository. Reassess license obligations before redistribution or hosted modification.
- Monitoring images are reproducibility pins, not an assertion of current patch status. No cloud accounts or paid resources provisioned.
- No scanner suppressions or allowlists were added for this project. Existing repository configuration, if any, remains unchanged.
- Host-only Python quickstart skipped because host Python is 3.9. Standalone Docker Python 3.11 path passed. Initial incorrect container mount was corrected; SSH fetch fallback is documented above. No failed experiment results are reported as measurements.

## Intentionally retained public information

Approved public repository/owner identity and GitHub noreply author metadata, public dependency/image names/digests, synthetic tenant/application/model/trace/request identifiers, synthetic prices/facts, reviewed CPU count, Docker memory budget, architecture, Python/OS versions and benchmark evidence. No home directory, real customer data, hostname, private email or real account identifier is intended for retention. Scanner output remains local and is summarized without raw findings.

## Verdict and publication record

- Local engineering reference: executable and verified, with documented simulation/security limits.
- Production deployment: NOT READY; demo authentication, retention, storage and exporters are intentionally local.
- Publication: **HOLD — explicit owner approval required; no push, merge or publication authorized.** Refresh comparison scope and repeat final-range review before any future publication, including inherited commits and report/fix commits.
- Scanners/manual review do not guarantee absence of every leak or vulnerability. Current dependency advisory results are time-bounded.
- Exact post-commit scan evidence follows after execution; no remote branch/SHA verification applies because nothing has been pushed.

## Post-commit and final staged review evidence

Implementation and final-snapshot outcomes are added only after their checks execute.

- Initial full index snapshot scan: PASS, exit 0, no leaks found (about 1.78 MB scanned). Final snapshot is rescanned after this evidence is staged.
- Exact changed-file review: 55 staged files confined to Project 05 and its two audit/index files. No modifications to Projects 01–04. Initial CRLF whitespace findings in generated CSV/text were corrected in the writer and artifacts; subsequent `git diff --cached --check` passes.
- Privacy review: no personal home paths or private email patterns in staged changes; no unintended runtime/database/cache artifacts. Public author metadata remains the established noreply identity. Metrics cardinality, payload-free storage/logging and synthetic fixture provenance reviewed.
- Final engineering execution: 33 tests passed, zero failures/skips; quick 80 and full 900 requests. Artifact arithmetic and trace-parent verification pass. Rate-limit integration test covers HTTP 429 and its admission denominator; benchmark runs deliberately remain below quota.
- Live stack: all ten scenarios passed real HTTP checks; Prometheus scraped generated metrics and returned stored request counts; Grafana database health passed and provisioning logs recorded successful completion. The verifier now waits up to 20 seconds for asynchronous scraping after startup, correcting an initial timing race.

- Exact implementation SHA scanned: `ed96d3559d556bc46595d30453113b97d4e5e799`; exact implementation tree: `92f61981669bda03fbf09c11ed3a8cc5f88b8a13`.
- Final pre-implementation-commit index snapshot: Gitleaks v8.30.1 immutable image above, `dir /scan --redact --no-banner`, exit 0, about 1.79 MB, no leaks. This includes the complete then-staged audit evidence.
- Implementation range: `8dfbd27fb9b18ea08d1cf863c85bdd43db30140e..ed96d3559d556bc46595d30453113b97d4e5e799`; Gitleaks `git /repo --log-opts=origin/main..HEAD --redact --no-banner`, exit 0, ten commits, about 1.79 MB, no leaks. Nine inherited commits and implementation author/committer metadata reviewed; all use the established public owner/noreply identity.
- This evidence-only follow-up changes the audit record and verification summary, not implementation or experiments. Its full index snapshot is rescanned before committing, and the complete main-to-final-HEAD range is scanned after committing. The exact final audit-record SHA and execution result are retained in the final delivery and ignored local audit receipt; this file does not claim to embed its own SHA.
- Publication remains HOLD solely for explicit owner authorization and fresh publication-time scope/review. No push, merge, release or cloud deployment was performed. Existing OS/image-scan and production-scope limitations remain as stated above.
