# Enterprise RAG benchmark

Dataset 1.0.0; 10 pipeline questions; 10 independently authored controlled answers. All data synthetic. Small samples are diagnostic, not production estimates.

Mode: lexical-only. Skipped methods: dense, hybrid.

| Method | N scored | Recall@K | Precision@K | MRR | nDCG@K | Median ms | P95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| bm25_local | 10 | 1.0000 | 0.3667 | 0.7667 | 0.8262 | 0.0916 | 0.1562 |

## Answer evaluation

| Source | N | Fact precision | Fact recall | Claim support | Citation precision | Citation coverage | Abstention accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|
| bm25_local | 10 | 0.5000 | 0.9000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| fixture | 10 | 0.5000 | 0.5000 | 0.6875 | 0.6250 | 0.5625 | 0.7000 |

## Category detail

Complete category metrics and per-metric denominators are in metrics.json; per-question and fixture rows are in the CSVs.
- bm25_local / cost: n=2; recall=1.0; fact recall=1.0; abstention accuracy=1.
- bm25_local / governance: n=2; recall=1.0; fact recall=1.0; abstention accuracy=1.
- bm25_local / incident: n=2; recall=1.0; fact recall=1.0; abstention accuracy=1.
- bm25_local / quality: n=2; recall=1.0; fact recall=1.0; abstention accuracy=1.
- bm25_local / sre: n=2; recall=1.0; fact recall=0.5; abstention accuracy=1.

## Interpretation and limits

Closed-world manually adjudicated exact claim identity; unknown claims conservatively receive zero support/correctness and are counted. Not a general factuality verifier. Null metrics excluded from macro means; empty claims have undefined precision/support; unanswerable cases have undefined retrieval metrics unless conflict qrels exist.

Sequential warmed serial queries; retrieval includes tokenization/query embedding/fusion, excludes index build; pipeline adds evidence selection and extractive generation, excludes evaluation and report I/O. P95 nearest rank; each query repeated; method order fixed (thermal/order confounder).

Index build: 0.212 ms. Peak process RSS: 32702464 bytes (whole process high-water mark, not per-method incremental memory). No API charges; CPU/energy opportunity cost is not zero and is not priced here.

The baseline copies up to two current retrieved chunks. It can cite irrelevant material perfectly, miss required facts, ignore active contradictions, and fail to abstain. Controlled fixtures test scoring independently from retrieval. Same-corpus development results are not held-out generalization evidence. No local generative LLM is required or measured.

For alternative chunk sizes, qrels remain atomic passage-level labels. Siblings are collapsed before K; any returned fragment counts as retrieving that passage (optimistic for fragmented evidence). Claim scoring remains exact authored text: split claims become unadjudicated, so chunk-sweep answer scores are not directly comparable without new human labels.

Hardware, versions, dataset hashes, configuration and UTC run times are recorded in metrics.json. Raw warmed latency samples are retained. See failure_analysis.md for observed failure classes.
