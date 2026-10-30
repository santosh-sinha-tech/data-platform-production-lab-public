# Project security audit index

Every project follows the repository-wide [security and privacy policy](../../SECURITY.md). New projects must add a report here using the [audit template](../security-audit-template.md); later releases must update the record. This index distinguishes earlier recorded evidence from checks performed now.

| Project | Existing evidence | Recorded scope/status | Remaining qualifications |
| --- | --- | --- | --- |
| 01 — Green Pipeline, Bad Data | [Release verification](../../projects/01-green-pipeline-bad-data/architecture/verification.md) | Historical verification records a redacted Gitleaks scan of the reviewed clone's reachable history with no leaks reported. | The document does not specify native versus Docker execution. This row is not a new scan or a dependency audit. |
| 02 — Small Files Performance Lab | [Publication review](../../projects/02-small-files-performance-lab/results/publication-review.md); recorded audit in the Project 02 development chat | Historical chat execution records Docker Gitleaks, redacted, exit 0, over `origin/main..HEAD`, covering two published Project 02 commits at that time; no leaks reported. Separate privacy and tracked-file checks were recorded. | The historical image used `latest`; an immutable digest was not recorded in that chat command. This row does not extend the scan to later commits or all repository history. |
| 03 — Enterprise RAG Evaluation Lab | [Project audit record](03-enterprise-rag-evaluation-lab.md); [verification and audit limitations](../../projects/03-enterprise-rag-evaluation-lab/architecture/verification.md) | Docker Gitleaks history/staged-tree scans and privacy checks passed; remediated dependency audit: 65 packages, zero known findings/skips. Python 3.11 tests and three-method benchmarks passed. | Release candidate `5f4af81` passed five-commit history and full-tree scans. Final audit-record commits are scanned before pushing; see the report for exact scope and limitations. |

## New project checklist

1. Read `SECURITY.md` and `AGENTS.md` before implementation.
2. Keep secrets/private inputs out of the project from the start; use synthetic examples and ignored local caches/outputs.
3. Copy the report template to `docs/security-audits/NN-project-name.md`.
4. Execute and document staged privacy/artifact review and applicable engineering/dependency checks.
5. Use native or Docker Gitleaks for the required tree and publication-history scans; include inherited unpublished commits.
6. Record known public metadata, findings/remediation and all failed/skipped checks. Keep publication on HOLD while required checks remain unresolved.
7. Review and scan subsequent report/fix commits, obtain explicit publication authorization, and verify the remote SHA after any authorized push.

Projects 01 and 02 retain their original files and historical evidence. New reports supplement history; they do not retrospectively claim stronger audits than were actually performed.
