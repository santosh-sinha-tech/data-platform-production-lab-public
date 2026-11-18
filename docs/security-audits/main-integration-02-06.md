# Main integration audit — Projects 02–06

## Scope and authorization

- Review date: 2026-11-18, Asia/Kolkata. Reviewer: Codex for the repository owner.
- Owner explicitly authorized merging Projects 02–06 into main in this chat. This supersedes earlier feature-branch-only restrictions for this integration; it does not authorize cloud deployments, tags, force pushes or branch deletion.
- Destination: `santosh-sinha-tech/data-platform-production-lab-public`, verified public; default target `main`.
- Refreshed exact base: `8dfbd27fb9b18ea08d1cf863c85bdd43db30140e`.
- Published cumulative candidate: `fe5d72b696f5cb63a1795f489ac4a38e8d9b7f40`, 15 commits ahead of base. All five published Project 02–06 branch heads are ancestors of this candidate. No separate project merges or file moves are needed.
- Integration branch: `codex/merge-projects-02-06`, based on that candidate. Its final audit/remediation commit is included in the full pre-push scan; exact final head, PR and merge SHA are verified and returned in the delivery, avoiding a self-referential report SHA.
- Scope: all tracked files plus the complete base-to-head comparison history, including inherited commits and this report/remediation commit. This is not an all-reachable-history scan before the comparison base.
- Project 01 is byte-for-byte unchanged from main. Projects 03–06 application source and benchmark results are unchanged from their published heads; audit documents gain this integration pointer. The only Project 02 executable-environment change is the patched pytest test dependency.

## Executed verification

| Project | Fresh test outcome | Evidence checks / qualification |
|---|---|---|
| 02 | 37 passed, 0 skipped with pytest 9.2.0 | Real local Spark generation, fragmented/compacted equivalence and queries; dependency consistency passed |
| 03 | 16 passed, 1 skipped | Actual pinned rank-bm25/numpy lexical backend; retained full benchmark quantiles, retrieval/answer/category denominators reconcile. Optional dense/model test intentionally not rerun; previous full dense/hybrid results remain historical evidence |
| 04 | 32 passed, 0 skipped | Retained benchmark attribution, variability and nine failure-scenario invariants reconcile |
| 05 | 33 passed, 0 skipped | Retained full 900 and quick 80 request metrics, dimensional cost and trace-parent correlations reconcile |
| 06 | 96 passed, 0 skipped | All retained 960 scenario samples, 16 outcomes, quantiles, retry/duplicate/recovery/wait and cost calculations reconcile |

Total final targeted suites: 214 passed, 0 failed, 1 intentionally skipped optional dense integration test. No new performance measurements or cloud execution are claimed. Previously measured benchmark artifacts are retained rather than regenerated for a source-preserving integration.

Commands used container-mounted source and the existing reviewed project images. Project 02 used `02-small-files-performance-lab-lab:latest`, installed exact `pytest==9.2.0`, then `python -m pytest -q` and `pip check`. Project 03 used an isolated temporary Python 3.11 venv with exact pytest 9.2.0, rank-bm25 0.2.2 and numpy 2.2.6; `python -m pytest -q -p no:cacheprovider`, `python scripts/validate_reports.py results`, then `pip check` without the source PYTHONPATH. Projects 04–06 used their existing images with current mounted source, pytest and their retained-artifact validators. Project 04 used `GATEWAY_SERVE=0` for test mode.

An initial Project 03 partial-stack harness ran 16 tests successfully but its general pip check failed because inherited full-project metadata declared intentionally omitted dense dependencies. A fresh isolated lexical venv resolves the harness contamination; no full dense-stack installation/consistency pass is claimed. The dense backend is unchanged and its retained three-method reports validate; it is explicitly outside this refresh's runtime population.

## Dependency review and remediation

Fresh pip-audit 2.10.1 scans used `--no-deps --disable-pip --format json` against complete exact-version project manifests. Project 03 hash-lock pins were extracted and the official Torch CPU version suffix normalized for upstream advisory lookup, matching its documented audit method; this does not replace binary hash verification.

Initial Project 02 scan found one unique known advisory, `PYSEC-2026-1845`, on test-only pytest 8.3.5 (scanner listed the advisory twice). Updated the pin to pytest 9.2.0 and reran all 37 Spark/unit tests successfully. Fresh post-remediation results:

| Project | Audited pinned package entries | Known findings | Skips |
|---|---:|---:|---:|
| 02 | 6 | 0 | 0 |
| 03 | 65 | 0 | 0 |
| 04 | 26 | 0 | 0 |
| 05 | 25 | 0 | 0 |
| 06 | 25 | 0 | 0 |

These are 147 per-project entries with overlap, not 147 unique packages. Hash locking is limited to the documented Project 03 platform; other manifests are exact-version pins. Container OS CVE scanning, re-downloading/verifying the dense model and rebuilding every image were not performed or claimed.

## Dedicated secret scanning

Native Gitleaks is unavailable; Docker fallback uses Gitleaks v8.30.1 pinned to `ghcr.io/gitleaks/gitleaks@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f`.

Fresh initial full comparison scan `git /repo --log-opts=8dfbd27fb9b18ea08d1cf863c85bdd43db30140e..fe5d72b696f5cb63a1795f489ac4a38e8d9b7f40 --redact --no-banner`: PASS, exit 0, 15 commits, no leaks. Final staged tracked-tree export and the final complete base-to-integration-head history are scanned before push, including this report and the dependency fix. Scan commands are pinned Docker `dir /scan --redact --no-banner` and `git /repo --log-opts=BASE..HEAD --redact --no-banner`. Exact final head/outcomes are confirmed in delivery. No raw scanner reports or suppressions are committed.

## Privacy, identity and artifact review

Reviewed all 346 originally tracked files and the new integration files. Initial full-tree inventory found zero personal home paths, credential-bearing URLs, private-key or phone patterns; the sole email token was the documented synthetic `.invalid` fixture. Manually authored synthetic datasets and reviewed benchmark metadata are retained. No runtime/SQLite files, environments, caches or credential directories are tracked. Root README links all six numbered project directories.

All 15 original candidate commits use established public owner identity and GitHub noreply author/committer addresses; integration commit metadata is checked before push. Intentionally public metadata: owner/repository identity, synthetic resource/tenant/UUID fixtures, dependency/model names and digests, benchmark environment/date/architecture and finite malicious-output examples. No private customer data or raw logs are introduced. Staged diff, full comparison whitespace and Project 01 scope checks are required before the final commit/push.

## Verdict and merge procedure

PASS for consolidating the educational reference labs into main after the final staged-tree and integration-commit scans complete. No known finding is waived. Create one pull request from the integration branch into main and merge using a merge commit with the verified expected head, preserving audited feature history. Confirm the merge is recorded and remote main exposes all six project directories. Existing feature branches are retained; no force push or deletion is needed. Post-merge remote main/commit verification is returned in delivery. Production deployment readiness is not implied; the individual project limitations remain in force.
