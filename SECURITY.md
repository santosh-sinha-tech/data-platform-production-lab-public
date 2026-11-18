# Public repository security and privacy policy

This policy applies to every current and future project under **Santosh Sinha Tech / Data Platform Production Lab**, including later edits to already reviewed projects. The repository is intended for public access. Every commit must be treated as content that may become permanently public.

The objective is to prevent disclosure of credentials, private information, customer data and unintended artifacts. A successful scan is bounded evidence, not a guarantee that no security issue exists. Documentation must distinguish checks actually executed from required, failed or skipped checks.

## Required review for every project and change

Before committing, review the exact staged file list and diff, not only the files most recently edited:

- Secrets: API keys, access/refresh tokens, passwords, private keys, certificates containing private material, service-account files, credential-bearing URLs, database connection strings and credentials embedded in notebooks or test fixtures.
- Privacy: personal home paths, private email addresses, phone numbers, account/project identifiers, internal URLs/hostnames/IPs, real business information and copied customer or employee records. Review screenshots, PDFs, diagrams, metadata and exported documents as well as source code.
- Data provenance: use synthetic examples; document how datasets were authored or generated. Review any external inputs for rights and privacy before inclusion. Public source availability alone does not establish permission to redistribute.
- Artifact hygiene: exclude local environments, model/package caches, generated bulk datasets, raw runtime logs, editor files, credential directories and unreviewed local reports. Only intentional, reviewed and reasonably sized evidence belongs in Git. Do not assume `.gitignore` removes files already tracked.
- Identity: inspect author and committer metadata for every unpublished commit. Use the established public owner identity and GitHub noreply address; do not expose a private mailbox.
- Dependencies and executable artifacts: review new dependencies, model sources, licenses and downloads; pin versions and immutable model/image identities where practical. Run an ecosystem vulnerability audit when dependencies change. Never describe a secret scan as a dependency audit. Do not execute downloaded model code without review.
- Engineering evidence: run relevant tests and report validation; check Git whitespace and confirm unrelated projects were not changed. Record failures and skipped checks honestly.

Expected public metadata can include the public repository identity, approved author identity, public dependency/model IDs, synthetic identifiers and reviewed benchmark environment/timestamps. Record exactly what is intentionally retained in the audit report. Redact personal paths, usernames and hostnames from benchmark output before committing.

## Secret scanning and publication gates

Run a dedicated secret scanner such as **Gitleaks** on the staged snapshot before the initial public release of a project and after security-sensitive changes. Before **every push/publication**, scan the complete commit range being published, including inherited unpublished commits and subsequent fixes. Use redacted output. Pattern searches and manual review complement this scan and do not replace it.

If the native executable is absent, use **Docker-based Gitleaks**, as recorded for Project 02. Check Docker availability before declaring the scanner unavailable. Record the actual scanner version and image digest; the historical Project 02 command used the `latest` tag, so the tag alone is not an immutable identity.

If a required scan fails or cannot run, mark publication **HOLD** and resolve the blocker. Never publish on the strength of a partial scan presented as complete. Existing user authorization and publication scope still apply; the scanner does not grant permission to push or merge.

### Establish scope before scanning

Run from the repository root. Read-only checks:

```bash
git status --short
git diff --cached --name-status
git diff --cached --check
git remote -v
git branch --show-current
```

Refresh remote references when network access is available, then choose the actual review target, for example `origin/main`. Do not silently substitute a different base or rely on a stale cached reference without disclosure. Record both base and head SHAs and inspect all unpublished commit metadata:

```bash
AUDIT_BASE=origin/main  # Example only: use the verified target for this publication.
git rev-parse --verify "${AUDIT_BASE}^{commit}"
git rev-parse HEAD
git log --format='%h | %an | %ae | %cn | %ce' "${AUDIT_BASE}..HEAD"
git diff --stat "${AUDIT_BASE}...HEAD"
```

A feature branch may include commits inherited from another project branch. Audit every commit that the push will newly expose, even when the project-only diff is smaller. For the first public release, or when a trustworthy baseline is unavailable, explicitly audit all reachable history and the final tracked tree; report that expanded scope. Review PR descriptions, release notes and attachments separately before publishing them.

### Scan the staged file snapshot

This exports the index to a temporary directory, including staged additions and edits. It does not expose ignored working files to the scanner or change source files. The temporary directory can contain sensitive findings: keep it local and remove the exact directory after review.

```bash
AUDIT_SNAPSHOT=$(mktemp -d)
git checkout-index --all --prefix="${AUDIT_SNAPSHOT}/"
# Native route:
gitleaks dir "$AUDIT_SNAPSHOT" --redact --no-banner
```

Docker alternative, with an already available or approved downloaded scanner image:

```bash
# Resolve this tag to an immutable identity; use the resulting digest for the audit.
AUDIT_IMAGE=$(docker image inspect ghcr.io/gitleaks/gitleaks:latest --format '{{index .RepoDigests 0}}')
docker run --rm \
  -v "${AUDIT_SNAPSHOT}:/scan:ro" \
  "$AUDIT_IMAGE" dir /scan --redact --no-banner
```

If image inspection fails or returns no digest, stop and obtain/verify the image through the normal approved dependency-download process. Do not continue with an empty image variable or claim a scanner run occurred.

### Scan the unpublished commits

After committing the reviewed changes, use the verified base from above. Choose one available route:

```bash
# Native route:
gitleaks version
gitleaks git . --log-opts="${AUDIT_BASE}..HEAD" --redact --no-banner

# Docker route (AUDIT_IMAGE is the verified digest resolved above):
docker run --rm "$AUDIT_IMAGE" version
docker run --rm \
  -v "${PWD}:/repo:ro" \
  "$AUDIT_IMAGE" git /repo \
  --log-opts="${AUDIT_BASE}..HEAD" --redact --no-banner
```

For an explicitly scoped full reachable-history scan, replace the log options with `--log-opts=--all`. History scanning and final-tree review serve different purposes: a secret removed by a later commit can remain in history. Conversely, staged edits are not yet covered by a commit-history scan.

Do not commit raw scanner output, discovered secret values, or reports containing private information. Audit reports should contain tool/version, scope, exit status, finding counts/categories and remediation status. Any scanner suppressions or allowlists require narrowly scoped justification and review; do not suppress an entire project to obtain a passing result.

## Audit evidence for each project

Create `docs/security-audits/NN-project-name.md` from the [audit report template](docs/security-audit-template.md) for each new project. Update it for each release or meaningful follow-up change and add it to the [audit index](docs/security-audits/README.md). An existing project's earlier pass does not cover later changes.

Record project and repository paths, review date, target/base SHA, exact scanned head SHA, final-tree/staged snapshot scope, scanner version/digest, commands, outcomes, privacy review, dependency checks, test results, intentionally public metadata and unresolved blockers. Until all required publication checks pass, the verdict is **HOLD**. The report commit itself and any fixes must also be included in the final pre-push review/scan; an audited implementation SHA must not be presented as covering later unreviewed commits.

Historical summaries are evidence pointers, not newly executed audits. Do not claim a particular scanner invocation or historical scope without a supporting record.

## Responding to a suspected leak

Stop the affected publication. Do not repeat a secret in chat, an issue, a commit message or an audit report. Identify only its category and safe location/context. Revoke or rotate exposed credentials with the owner; deleting the current file does not revoke a credential or erase Git history. Coordinate review of access logs and affected services where applicable.

History rewriting, force pushes, removal of shared branches and changes to repository visibility require explicit owner authorization. Keep private incident details out of public GitHub issues. This repository does not designate a private reporting mailbox; use an existing private owner contact channel rather than posting sensitive evidence publicly.

## Authorization boundary

Commit locally only after the required staged review. Push, publish, merge and release only within explicit owner authorization. Approval to push a feature branch does not authorize merging it into `main`. Verify the exact destination repository, branch, visibility and remote commit after an authorized push. Preserve an accurate record of checks not executed.
