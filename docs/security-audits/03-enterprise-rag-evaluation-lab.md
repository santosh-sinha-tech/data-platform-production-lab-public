# Security and privacy audit — Project 03: Enterprise RAG Evaluation Lab

## Scope and release identity

- Review date: **30 October 2026 (Asia/Kolkata)**.
- Project: `projects/03-enterprise-rag-evaluation-lab/`.
- Public destination: `santosh-sinha-tech/data-platform-production-lab-public`.
- Authorized branch: `feat/03-enterprise-rag-evaluation-lab`; no merge into `main` authorized.
- Refreshed comparison base: `origin/main`, SHA `8dfbd27fb9b18ea08d1cf863c85bdd43db30140e`.
- Initial audited implementation head: `3afdeb3a8726c54bad59e321b87f3f0a93f67445`.
- History scope: all commits in `origin/main..HEAD`, including inherited Project 02 commits, the standing-instruction commit, Project 03 implementation, and subsequent verification/documentation/fix commits. Project 01's original history is outside this range; its final tracked files are included in the tree review.
- The final report/verification commit must be scanned after committing and before pushing. Its exact publication SHA is verified against GitHub and supplied in the publication confirmation; the report cannot embed the SHA of its own containing commit.

## Executed checks

| Check | Actual outcome | Scope/qualification |
| --- | --- | --- |
| Initial dedicated history scan | PASS, exit 0, no leaks reported | Four commits from refreshed `origin/main` through implementation head `3afdeb3`; final follow-up commits require another scan |
| Dedicated staged-tree scan | PASS, exit 0, no leaks reported | 231 tracked/proposed public files, 1,137,150 bytes at the first snapshot; includes all three projects and proposed portfolio/security documents |
| Privacy and size review | PASS | Entire staged tree checked for supported personal-home-path, private-mailbox, credential-URL, private-key and private-IP patterns; no findings; no individual file >1 MB |
| File/artifact and scope review | PASS | Synthetic datasets and compact measured evidence retained; no environments, caches, raw logs or credentials staged; Projects 01/02 unchanged from the starting Project 03 commit |
| Commit metadata | PASS | Unpublished commits use the established public owner name and GitHub noreply identity; rechecked before publication |
| Dependency lock/install | PASS | Linux ARM64/Python 3.11 CPU requirements hash-locked; installed with `--require-hashes`; `pip check` passed |
| Dependency audit | PASS after remediation | 65 third-party packages, zero known findings, zero skipped packages; see normalization below |
| Engineering validation | PASS | Python 3.11.11, 17 tests passed, zero failures/skips; quick/full actual BM25, dense and hybrid evaluations and CSV/JSON reconciliation passed |
| Documentation and Git whitespace | PASS | Local links resolve; staged whitespace checks pass |

## Scanner identity and commands

Gitleaks **v8.30.1**, executed through Docker Engine 28.3.2. Immutable scanner image:

`ghcr.io/gitleaks/gitleaks@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f`

Native scanner was absent; the existing Docker scanner used for Project 02 was available. No image download or scanner allowlist/suppression was needed. Output was redacted; no raw findings or secret values are committed.

From repository root, with the index exported to a private temporary snapshot:

```bash
AUDIT_IMAGE=ghcr.io/gitleaks/gitleaks@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f
docker run --rm "$AUDIT_IMAGE" version
AUDIT_SNAPSHOT=$(mktemp -d)
git checkout-index --all --prefix="${AUDIT_SNAPSHOT}/"
docker run --rm -v "${AUDIT_SNAPSHOT}:/scan:ro" "$AUDIT_IMAGE" dir /scan --redact --no-banner
docker run --rm -v "${PWD}:/repo:ro" "$AUDIT_IMAGE" git /repo --log-opts=origin/main..HEAD --redact --no-banner
```

The last command is repeated after committing all reviewed changes; publication is conditional on its successful exit and final tree recheck. This does not claim a fresh full-history scan of every Project 01 commit.

## Findings and remediation

No secrets were reported by the dedicated scans described above. Separate privacy review found no supported-pattern issues. Git author/committer identity and public benchmark metadata are intentionally retained.

The initial installed-environment dependency audit found **10 advisories across pip 24.0, pytest 8.3.5 and setuptools 78.1.0**. Remediated to pip 26.2.2, pytest 9.0.3 and setuptools 84.1.0, including the build-backend pin. Regenerated/reinstalled the complete hash lock, reran all 17 tests, and reran the dependency audit successfully.

The official Torch CPU build `2.15.0+cpu` is normalized to upstream `2.15.0` for PyPI advisory lookup. This is explicitly recorded in `results/dependency_audit.json`; it does not attest to binary integrity. Downloaded wheels are independently constrained by the lock's hashes. The local repository package is excluded from the PyPI advisory query and reviewed/tested as source. Model safetensors checksum/revision and remote-code setting are recorded in `results/model_manifest.json`.

An initial default Torch download began resolving unused CUDA libraries and was stopped. Only the official CPU build is installed in the verified environment/lock. The dependency installer, test and benchmark outputs are not raw tracked runtime logs.

## Intentionally retained public information

Public repository identity; established owner name/GitHub noreply commit identity; public model, package and scanner IDs/digests; synthetic scenarios; OS/architecture/CPU/RAM/cgroup constraints; software versions and UTC benchmark/audit timestamps. No personal home paths, private mailboxes, hostnames or private customer records were found in the reviewed public tree. Local cache/working paths are not exported in benchmark metadata.

## Limits and publication record

Checks are point-in-time evidence, not proof that all leaks or vulnerabilities are absent. No OS/container vulnerability scan, independent human SME label review, held-out enterprise benchmark or production/cloud security assessment was performed. These limitations remain explicit in the project documentation.

The user explicitly authorized pushing this feature branch and sharing the public Project 03 URL. The existing GitHub CLI account/destination public visibility were verified; SSH host-key verification failed, so verified HTTPS transport is used without disabling SSH verification. Final audited candidate SHA and follow-up report scan are recorded below when complete. `main` and the published Project 02 branch remain unchanged.

**Verdict: implementation/dependency checks and initial security scans PASS; complete the final report-commit history/tree scans before the authorized feature-branch push.**
