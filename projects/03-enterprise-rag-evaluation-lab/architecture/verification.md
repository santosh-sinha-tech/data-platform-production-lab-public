# Release verification — Project 03

Verified on **30 October 2026 (Asia/Kolkata)**. All data is synthetic. This is a local reference implementation, not a production service certification.

## Current outcome

- **17 tests passed, zero failures/skips**, including real rank-bm25, dense and hybrid integration, on Python 3.11.11 / pytest 9.0.3.
- Quick and full evaluations executed with **all three retrieval methods** and the pinned MiniLM model.
- Independent report reconciliation passed for both runs, including aggregate/category scores, answer denominators and latency samples/median/P95.
- Complete Linux ARM64/Python 3.11 **CPU** dependency lock generated with wheel hashes; locked installation and `pip check` passed.
- Dependency audit after remediation: **65 third-party packages, zero known findings, zero skipped packages**, with the official Torch CPU suffix normalized to its upstream advisory version. See `results/dependency_audit.json`.
- Publication secret/privacy review and exact Git scope are recorded in the [project security audit](../../../docs/security-audits/03-enterprise-rag-evaluation-lab.md). The final history scan must also cover the report/fix commits.
- User authorized publishing the Project 03 feature branch. No merge into `main` is authorized.

## Runtime and resource provenance

The release used an isolated venv inside the existing local Project 02 runtime image, without changing Project 02 files or its image. Image ID: `sha256:c5508ff3bfd022207f85528a75aee53dd0deb11842952554d8ba841d44be6bb8`. Spark was not used. The Python base was 3.11.11; the disposable environment had no enterprise credentials.

Docker Engine 28.3.2; Linux aarch64, Docker Linux VM. Container limited to **2 CPUs / 4 GiB RAM**, with `OMP_NUM_THREADS=2` and `MKL_NUM_THREADS=2`. Host-visible VM resources are recorded separately in metrics.json: 10 logical CPUs / 8,218,034,176 bytes RAM. The cgroup CPU quota is `200000 100000`, memory limit `4294967296`. Full-run peak process RSS was 552,247,296 bytes; this is a process high-water mark, not a per-backend incremental allocation.

The model was downloaded once from the pinned immutable public revision, then final tests/benchmarks used `HF_HUB_OFFLINE=1`. `results/model_manifest.json` records the downloaded 90,868,376-byte safetensors weight file and SHA-256 `53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db`. Remote code was disabled. The checksum is measured content identity, not an independent security attestation.

## Exact release commands

Inside the disposable container, from the Project 03 directory:

```bash
python -m venv /tmp/rag-venv
/tmp/rag-venv/bin/python -m pip install torch==2.15.0+cpu --index-url https://download.pytorch.org/whl/cpu
/tmp/rag-venv/bin/python -m pip install -e '.[test]'
/tmp/rag-venv/bin/python -m pip install --target /tmp/rag-lock-tools uv==0.9.7
/tmp/rag-lock-tools/bin/uv pip compile pyproject.toml --extra test \
  --python-version 3.11 --python-platform aarch64-unknown-linux-gnu \
  --extra-index-url https://download.pytorch.org/whl/cpu \
  --index-strategy unsafe-best-match --generate-hashes --no-emit-index-url \
  -o requirements-linux-arm64.lock
/tmp/rag-venv/bin/python -m pip install --require-hashes --no-deps \
  --extra-index-url https://download.pytorch.org/whl/cpu \
  -r requirements-linux-arm64.lock
/tmp/rag-venv/bin/python -m pip check
HF_HUB_OFFLINE=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 RAG_TEST_DENSE=1 \
  /tmp/rag-venv/bin/python -m pytest -q
HF_HUB_OFFLINE=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  /tmp/rag-venv/bin/python -m rag_lab.runner --mode quick --output results/quick
HF_HUB_OFFLINE=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  /tmp/rag-venv/bin/python -m rag_lab.runner --mode full --output results
/tmp/rag-venv/bin/python scripts/validate_reports.py results
/tmp/rag-venv/bin/python scripts/validate_reports.py results/quick
/tmp/rag-venv/bin/python scripts/audit_dependencies.py
```

Final pytest output: `17 passed in 5.92s`. The initial real-model integration pass, before the packaging-tool fixes, also passed 17 tests in 21.67s. The final run used the locked, remediated versions.

The lock compiler searched PyPI and the official PyTorch CPU index; the extra source is required for the CPU-specific Torch wheel. Hash verification succeeded. The lock targets Linux ARM64/Python 3.11 and is not claimed portable to other platforms. The local editable package is installed separately; its code/data are versioned in this repository rather than resolved from PyPI.

## Measured full-suite results

Eighteen questions; 16 have passage qrels (including an unanswerable active-conflict case), 15 have reference facts. Each query/method has 3 warmups and 15 measured repetitions. Controlled fixtures always include all 10 examples and are summarized separately.

| Method | Recall@3 | Precision@3 | MRR | nDCG@3 | Median retrieval ms | P95 retrieval ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BM25 | 1.0000 | 0.4375 | 0.7604 | 0.8118 | 0.0616 | 0.0914 |
| Dense | 1.0000 | 0.4375 | 0.9063 | 0.9308 | 9.6213 | 15.1532 |
| Hybrid RRF | 1.0000 | 0.4375 | 0.8125 | 0.8512 | 9.6396 | 15.4917 |

| Answer source | Fact precision | Fact recall | Claim support | Citation precision | Citation coverage | Abstention accuracy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BM25 pipeline | 0.4722 | 0.9333 | 1.0000 | 1.0000 | 1.0000 | 0.8333 |
| Dense pipeline | 0.5000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.8333 |
| Hybrid pipeline | 0.5000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.8333 |
| Controlled fixtures | 0.5000 | 0.5000 | 0.6875 | 0.6250 | 0.5625 | 0.7000 |

These are small descriptive development-set results. Dense improved ranking here; RRF did not outperform dense. Every pipeline answered all three cases requiring abstention/clarification. BM25 retrieved but did not select the needed SEV1 fact. Perfect citation support is possible for question-irrelevant copied text and therefore does not establish answer correctness. Exact denominators, category scores and samples are in the generated artifacts.

Retrieval timings include query encoding/fusion where applicable, exclude index construction, and use fixed method order. Full index construction, including model initialization, took 5,875.011 ms; dense vector storage was 27,648 bytes for 18 vectors. No CPU utilization, energy, currency cost or concurrent throughput measurement was taken. No other build/audit job ran during the measured query loops.

## Failures found and resolved

- Native Python 3.11 was absent and sandbox PyPI DNS failed in the initial attempt. The early offline diagnostic tests ran under Python 3.12.14/3.13.3. Those lexical-only measurements remain in Git history; current results replace them with the executed Python 3.11 three-arm comparison.
- Initial automatic approval review failed at model capacity. A later authorized publication turn obtained Docker/network execution approval; no sandbox check was bypassed.
- The default Linux Torch installation began pulling unnecessary CUDA libraries. That disposable attempt was stopped; the verified environment uses the official `2.15.0+cpu` wheel. No CUDA package is part of the CPU lock.
- Initial dependency audit found 10 advisories across pip 24.0, pytest 8.3.5 and setuptools 78.1.0. Updated pins to pip 26.2.2, pytest 9.0.3 and setuptools 84.1.0; regenerated/reinstalled the hash lock; reran tests and audit successfully. Build backend is pinned to the remediated setuptools version too.
- The default auditor could not match the local package or Torch's `+cpu` suffix on PyPI. The audit script excludes the repository's local package and explicitly maps Torch to upstream 2.15.0. The resulting 65-package advisory lookup skipped no third-party packages. Binary integrity, local source review and model review remain separate controls.
- CSV CRLF endings failed the first staged whitespace check. The writer and artifacts use LF; parsed measurements are unchanged.
- SSH Git access failed host-key verification. HTTPS fetch authenticated through the existing GitHub CLI is used instead; host-key verification was not disabled.

## Remaining limits and unexecuted checks

No independent human SME adjudication/inter-rater study, held-out enterprise corpus, arbitrary-paraphrase factuality verification, generative LLM adapter, concurrent serving load, OS/container vulnerability scan, cloud deployment or production SLO validation was performed. These remain limitations, not claims of completed checks. The model and dataset are intentionally tiny. Future dependency advisories can change; the audit records a point-in-time result.

Source labels were explicitly authored independently of the evaluated retriever/answerer, but external expert review has not occurred. Unknown claim text receives conservative zeros and an unadjudicated count. Alternate chunk sizes can make answer comparisons invalid without new fragment/claim labels, as documented in the architecture and reports.

Projects 01 and 02 have no file changes from the starting Project 03 implementation. Publication is limited to the authorized feature branch; `main` and the published Project 02 branch are not modified.
