# Release verification — 2026-10-30

## Verdict

**Local offline diagnostic implementation verified; public release held pending standard-environment verification.** No push, merge, publication or cloud deployment was performed. Projects 01 and 02 were not edited. Work is on `feat/03-enterprise-rag-evaluation-lab` in the public repository checkout.

## Executed environment and commands

The following are exact shell commands used, with interpreter variables assigned to the existing runtime locations for reproducibility on this machine. Absolute personal workspace paths are intentionally omitted from tracked evidence.

```bash
# Run from projects/03-enterprise-rag-evaluation-lab
BENCH_PY="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
TEST_PY="$HOME/Documents/ChatGPT/Project 03 - Home Buyer Support Agent/.venv/bin/python"
PYTHONPATH=src "$BENCH_PY" -m unittest discover -s tests -v
PYTHONPATH=src "$TEST_PY" -m pytest -q
PYTHONPATH=src "$BENCH_PY" -m rag_lab.runner --mode quick --lexical-only --local-bm25 --output results/quick
PYTHONPATH=src "$BENCH_PY" -m rag_lab.runner --mode full --lexical-only --local-bm25
"$BENCH_PY" scripts/validate_reports.py results
"$BENCH_PY" scripts/validate_reports.py results/quick
python3 scripts/release_checks.py
# From repository root
 git diff --check
 git diff --cached --check
 git diff --cached --name-only
```

Benchmarks/unittest: Python 3.12.14, Darwin arm64, 10 logical CPUs, 16 GiB physical RAM. Pytest: existing Python 3.13.3 environment with pytest 9.0.2, reused read-only; no changes made to that other project. The pinned project pytest dependency was not installed. Offline code is stdlib-only; installed NumPy version is recorded as metadata but not used by bm25_local.

| Check | Actual outcome |
|---|---|
| Unit/integration tests | 15 passed |
| rank-bm25 integration | Skipped: package unavailable |
| Real dense/hybrid model integration | Skipped: package stack/model unavailable |
| Quick evaluation | Executed, 10 questions, 2 warmups, 5 repeats/query; all 10 answer fixtures |
| Full evaluation | Executed in explicit lexical-only mode, 18 questions, 3 warmups, 15 repeats/query; all 10 fixtures |
| Independent CSV/JSON reconciliation | Passed both runs: retrieval aggregates/categories, answer means/denominators, latency samples/median/P95 |
| Reproducibility | Predictions and quality metrics identical across two independent quick runs; timing intentionally varies |
| Source/fixture privacy and size patterns | Passed scoped project review; no matched personal paths, email addresses, private IPs, credential URLs or supported token/key patterns |
| Git whitespace/scope | Initial staged check found CSV CRLF line endings; writer and artifacts corrected to LF, then passed. Only Project 03 plus repository README |
| Dedicated secret scanner | Not executed; Gitleaks unavailable. Mandatory before any future publication |
| pip-audit | Not executed; dependency environment unavailable |
| Python 3.11 install/test | Not executed: interpreter unavailable |
| Dense and hybrid benchmark | Not executed; no substitute or fabricated results |
| Full transitive hash lock | Not generated: network installation unavailable; direct versions only are pinned |
| Cloud/concurrency/production load test | Out of scope; architecture recommendations only |

## Failed checks and blockers

`python3.11 --version` failed: interpreter not on PATH; inspected available runtimes did not provide 3.11. A pip download of uv 0.9.7 to a temporary bootstrap directory failed to resolve PyPI in the sandbox. A network-enabled retry was not executed because automatic approval review failed at model capacity; this was not a safety rejection. User guidance/approval was requested. No permission bypass was used.

Default all-method execution was exercised and failed on missing rank-bm25; the CLI now gives an explicit dependency/fallback message. The fallback requires both `--lexical-only --local-bm25`, has a distinct method name, and marks dense/hybrid skipped. Dense initialization also has a clear error for missing packages/model. No credentials or local generative LLM were used.

## Dependency review

Initial candidate Torch 2.6.0 and Transformers 4.49.0 pins were rejected after checking public advisories, including [Torch memory corruption](https://github.com/advisories/GHSA-rrmf-rvhw-rf47), [Transformers ReDoS](https://github.com/advisories/GHSA-jjph-296x-mrcr), and [custom generation code consent](https://github.com/advisories/GHSA-x9r9-c232-4q39). Final candidate pins use sentence-transformers 6.2.0, Torch 2.15.0, Transformers 5.22.1, huggingface-hub 2.4.0 and safetensors 0.8.0. Release existence was checked on the corresponding public PyPI pages; sentence-transformers' versioned pyproject supports Transformers >=5,<6 and Hub >=1.3,<3. These are **uninstalled, unverified candidate pins**, not a clean dependency audit or compatibility proof. Resolve and hash-lock them in Python 3.11, run pip check/pip-audit, and execute model integration before release.

Model revision existence was checked against the official immutable Hugging Face tree. Runtime code forces safetensors and disables remote code. This reduces particular loading risks; it does not replace supply-chain scanning.

## Evidence interpretation

Full run: 16 of 18 questions have passage qrels (including one unanswerable conflict case); 15 have reference facts. Macro retrieval Recall@3=1.0, Precision@3=0.4375, MRR=0.7604167, nDCG@3=0.8117900. Baseline fact precision=0.4722222, fact recall=0.9333333, claim support=1.0, citation precision=1.0, citation coverage=1.0, abstention accuracy=0.8333333. It answered all three cases requiring abstention/clarification. The SEV1 case retrieves relevant evidence but does not select it within the two-passage evidence budget.

Controlled fixture macro scores: fact precision=0.5 (8 defined), fact recall=0.5 (7 defined), claim support=0.6875 (8), citation precision=0.625 (8), coverage=0.5625 (8), abstention accuracy=0.7 (10). These intentionally mixed positive/negative examples do not estimate production prevalence.

Latency samples and machine metadata are authoritative in metrics.json and latency_samples.csv. Fixed method order and serial execution are confounders. No CPU utilization, energy, currency cost or concurrent throughput measurement was taken. Peak RSS is a whole-process high-water mark.

## Publication audit scope and retained metadata

Audit covers the new project files and repository README, not the historical repository or other unpublished commits. Compact synthetic input datasets and reviewed measured result artifacts are intentionally tracked. Local environments, caches, raw runtime logs and unreviewed local run outputs are excluded. Public retained metadata: repository identity, established owner name/GitHub noreply commit identity, public model/package IDs, OS/architecture/CPU/RAM/library versions and run times. No usernames/hostnames/home paths are retained in benchmark artifacts. Pattern checks cannot prove absence of all secrets.

Before approval to publish: obtain Python 3.11 and dependencies/model; generate transitive hash lock; run pip check/audit and all backend tests; run both modes with all three methods; reconcile reports; get human review of labels; run Gitleaks across every unpublished commit against the intended target branch; repeat exact staged scope/privacy review. Then request explicit publication authorization.
