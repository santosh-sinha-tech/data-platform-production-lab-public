# Security and privacy audit — Project NN: project name

> Template only. Replace every placeholder; unchecked or pending items are not passing evidence. Never include raw secret values or private finding details.

## Scope and release identity

- Review date/time (with timezone): PENDING
- Reviewer: PENDING
- Project directory: `projects/NN-project-name/`
- Repository / destination visibility: PENDING
- Branch / intended review target: PENDING
- Verified base SHA: PENDING
- Exact implementation/head SHA scanned: PENDING
- History range / whether inherited unpublished commits are included: PENDING
- Staged/final tracked-tree snapshot reviewed: PENDING
- Scope exclusions and rationale: PENDING

## Executed checks

| Check | Exact command or review method | Tool version / image digest | Outcome and safe findings summary |
| --- | --- | --- | --- |
| Staged file list, diff and whitespace | PENDING | Git: PENDING | NOT RUN |
| Dedicated scanner: staged/final tree | PENDING | Gitleaks version/digest: PENDING | NOT RUN |
| Dedicated scanner: full unpublished commit range | PENDING | Gitleaks version/digest: PENDING | NOT RUN |
| Personal paths, contact details, internal identifiers and artifact metadata | PENDING | PENDING | NOT RUN |
| Credentials and unintended tracked files | PENDING | PENDING | NOT RUN |
| Synthetic data provenance and redistribution rights | PENDING | PENDING | NOT RUN |
| Author/committer identity across unpublished commits | PENDING | Git: PENDING | NOT RUN |
| Dependency/model/image provenance and vulnerability audit | PENDING | PENDING | NOT RUN |
| Tests and report/evidence validation | PENDING | PENDING | NOT RUN |
| Artifact sizes, generated data/log/cache exclusions | PENDING | PENDING | NOT RUN |
| Unrelated project diff | PENDING | Git: PENDING | NOT RUN |

Use PASS / FAIL / SKIPPED / NOT RUN. Explain skipped checks; do not imply they passed. Document whether Docker fallback was attempted when native Gitleaks was unavailable. For documentation-only changes, justify why dependency/runtime checks are unchanged while still performing the relevant privacy, diff and publication checks.

## Findings and remediation

- Safe finding categories/counts (no values): PENDING
- Remediation / credential rotation status if applicable: PENDING
- Suppressions/allowlists and justification: PENDING
- Re-scan scope/results following fixes: PENDING
- Failed or unexecuted checks and blockers: PENDING

## Intentionally retained public information

List approved author/repository identity, public dependencies, synthetic identifiers, benchmark resources/timestamps or other metadata. Explain exclusions or redactions: PENDING.

## Verdict and publication record

- Publication verdict: **HOLD — audit incomplete**
- Limits: scanners and manual review do not guarantee absence of all leaks or vulnerabilities.
- Owner authorization and exact approved action: PENDING; no publication authorized by this template.
- Final audited publication SHA/range, including report/fix commits: PENDING
- After an authorized push: remote branch/SHA/visibility verification: PENDING
