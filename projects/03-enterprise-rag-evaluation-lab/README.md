# Project 03 — Enterprise RAG Evaluation Lab

A synthetic reference implementation showing why retrieval relevance, answer correctness, groundedness and citation support require separate controls. It runs locally without credentials or paid APIs. There is no application UI or cloud deployment.

**Verification status:** the committed artifacts are actual offline lexical-only measurements. Dense and hybrid are implemented but were not executed because dependencies/model downloads were blocked; Python 3.11 verification and a complete transitive dependency lock remain open. See [verification](architecture/verification.md). Do not present these artifacts as a completed three-arm comparison.

The corpus contains incident runbooks, data-quality contracts, cloud-cost policy, SRE escalation, governance and architecture decisions, with stale versions, near duplicates, contradictions and missing/ambiguous evidence. There are 18 explicit question labels and 10 controlled answer fixtures. The extractive baseline does not see evaluation labels. Read [data provenance](data/PROVENANCE.md) and the [13-part architecture](architecture/architecture.md).

## Standard Python 3.11 setup

From this project directory:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m pytest -q
RAG_TEST_DENSE=1 .venv/bin/python -m pytest -q
.venv/bin/python -m rag_lab.runner --mode quick --output results/local-quick
.venv/bin/python -m rag_lab.runner --mode full --output results/local-full
.venv/bin/python scripts/validate_reports.py results/local-full
.venv/bin/python -m pip_audit
```

Direct dependencies are pinned; transitive resolution is not yet hash-locked. The standard installation and model loading have not been validated here. Dense requires the public MiniLM revision in retrieval.py; first load downloads roughly 91 MB of weights plus tokenizer/config and dependencies. Model loading uses CPU, safetensors and no remote code. Cache outside Git; set `HF_HOME` to a local cache and `HF_HUB_OFFLINE=1` after prefetch for disconnected runs. No other model is silently substituted.

## Explicit offline mode

If the package environment is unavailable, run from source with a Python interpreter:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m rag_lab.runner --mode quick --lexical-only --local-bm25 --output results/local-quick
PYTHONPATH=src python3 -m rag_lab.runner --mode full --lexical-only --local-bm25 --output results/local-full
python3 scripts/validate_reports.py results/local-full
```

This dependency-free diagnostic path was executed under Python 3.12.14. It is labeled `bm25_local`, uses positive Robertson IDF with k1=1.5/b=0.75, and is not presented as the rank-bm25 package or as dense retrieval. With rank-bm25 installed, omit `--local-bm25` to measure the library lexical arm. `--lexical-only` always marks dense/hybrid skipped. Default all-method execution fails clearly when the embedding stack is unavailable.

## Configuration and outputs

`--config PATH` accepts the JSON schema demonstrated in config/quick.json and config/full.json. Configure whitespace chunk size/overlap, K, evidence limit, RRF constant, seed, warmups, repetitions and question limit. Defaults: chunk 64 words, overlap 8, K=3, evidence limit 2. Quick runs 10 questions with 2 warmups/5 repeats; full runs 18 with 3 warmups/15 repeats. Both score all 10 controlled fixtures separately. The dataset is small by design; full means complete scenario coverage, not a scale benchmark.

Each output directory contains:

| Artifact | Purpose |
|---|---|
| metrics.json | Aggregates, category results, denominators, machine/library/configuration provenance |
| retrieval_comparison.csv | Per-question passage Recall/Precision/MRR/nDCG and latency |
| answer_evaluation.csv | Per-prediction correctness, support, citation and abstention metrics |
| predictions.json | Explicit claims, citations and selected evidence; separate from reference labels |
| latency_samples.csv | Every warmed repeated retrieval/pipeline timing sample |
| failure_analysis.md | Observed failures and engineering actions |
| benchmark_report.md | Measured comparison and methodological limits |

Committed full offline results are in results/ and quick results in results/quick/. Use results/local-* for unreviewed local output; these are ignored. See [full benchmark](results/benchmark_report.md) and [failure analysis](results/failure_analysis.md).

## Reading the metrics

Recall@K divides relevant retrieved passages by all positive qrels; Precision@K divides by configured K even when fewer results exist. MRR is reciprocal first-positive rank within K. nDCG uses `2^grade - 1` gain and log2 discounts, normalized by ideal positive grades. Chunk siblings collapse before K. No-qrel questions have undefined retrieval metrics and are excluded from macro means; active-conflict questions still have relevance labels. Rank ties are deterministic.

Answer fact precision is the fraction of emitted authored claims matching this question's reference facts; recall is coverage of expected distinct facts. This closed-world reference relevance/completeness score is not a general natural-language factuality verifier. Evidence support and citation support use separate authored claim/passage judgments. Unknown claim text receives conservative zero and an explicit unadjudicated count. A citation must both support its attached claim and belong to selected evidence. Citation coverage is the fraction of emitted claims with at least one valid supporting citation; citation precision is valid citations / all citations. Contradiction counts use explicit authored relations.

Empty-answer precision/support and zero-citation precision are undefined (`null`/blank), never automatically perfect. Macro means exclude undefined values and record denominators. Abstention correctness includes both false abstention and failure to abstain; appropriate-abstention and failure counts are also available per row. Fixture metrics remain separate from pipeline metrics.

The baseline can copy true but irrelevant facts and provide perfect citation support while answering the actual question poorly. It does not detect active conflicts or calibrate answerability. This is intentional failure visibility, not a claim of production readiness. Latencies are serial, warmed, small-corpus measurements; see the recorded protocol before comparing hardware or methods.
