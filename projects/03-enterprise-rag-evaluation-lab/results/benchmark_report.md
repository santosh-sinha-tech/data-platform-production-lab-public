# Enterprise RAG benchmark

Dataset 1.0.0; 18 pipeline questions; 10 independently authored controlled answers. All data synthetic. Small samples are diagnostic, not production estimates.

Mode: all. Skipped methods: none.

| Method | N scored | Recall@K | Precision@K | MRR | nDCG@K | Median ms | P95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| bm25 | 16 | 1.0000 | 0.4375 | 0.7604 | 0.8118 | 0.0616 | 0.0914 |
| dense | 16 | 1.0000 | 0.4375 | 0.9062 | 0.9308 | 9.6213 | 15.1532 |
| hybrid | 16 | 1.0000 | 0.4375 | 0.8125 | 0.8512 | 9.6396 | 15.4917 |

## Answer evaluation

| Source | N | Fact precision | Fact recall | Claim support | Citation precision | Citation coverage | Abstention accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|
| bm25 | 18 | 0.4722 | 0.9333 | 1.0000 | 1.0000 | 1.0000 | 0.8333 |
| dense | 18 | 0.5000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.8333 |
| hybrid | 18 | 0.5000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.8333 |
| fixture | 10 | 0.5000 | 0.5000 | 0.6875 | 0.6250 | 0.5625 | 0.7000 |

## Category detail

Complete category metrics and per-metric denominators are in metrics.json; per-question and fixture rows are in the CSVs.
- bm25 / ambiguous: n=1; recall=None; fact recall=None; abstention accuracy=0.
- bm25 / architecture: n=1; recall=1.0; fact recall=1.0; abstention accuracy=1.
- bm25 / conflict: n=1; recall=1.0; fact recall=None; abstention accuracy=0.
- bm25 / cost: n=3; recall=1.0; fact recall=1.0; abstention accuracy=1.
- bm25 / governance: n=3; recall=1.0; fact recall=1.0; abstention accuracy=1.
- bm25 / incident: n=3; recall=1.0; fact recall=1.0; abstention accuracy=1.
- bm25 / missing: n=1; recall=None; fact recall=None; abstention accuracy=0.
- bm25 / quality: n=3; recall=1.0; fact recall=1.0; abstention accuracy=1.
- bm25 / sre: n=2; recall=1.0; fact recall=0.5; abstention accuracy=1.
- dense / ambiguous: n=1; recall=None; fact recall=None; abstention accuracy=0.
- dense / architecture: n=1; recall=1.0; fact recall=1.0; abstention accuracy=1.
- dense / conflict: n=1; recall=1.0; fact recall=None; abstention accuracy=0.
- dense / cost: n=3; recall=1.0; fact recall=1.0; abstention accuracy=1.
- dense / governance: n=3; recall=1.0; fact recall=1.0; abstention accuracy=1.
- dense / incident: n=3; recall=1.0; fact recall=1.0; abstention accuracy=1.
- dense / missing: n=1; recall=None; fact recall=None; abstention accuracy=0.
- dense / quality: n=3; recall=1.0; fact recall=1.0; abstention accuracy=1.
- dense / sre: n=2; recall=1.0; fact recall=1.0; abstention accuracy=1.
- hybrid / ambiguous: n=1; recall=None; fact recall=None; abstention accuracy=0.
- hybrid / architecture: n=1; recall=1.0; fact recall=1.0; abstention accuracy=1.
- hybrid / conflict: n=1; recall=1.0; fact recall=None; abstention accuracy=0.
- hybrid / cost: n=3; recall=1.0; fact recall=1.0; abstention accuracy=1.
- hybrid / governance: n=3; recall=1.0; fact recall=1.0; abstention accuracy=1.
- hybrid / incident: n=3; recall=1.0; fact recall=1.0; abstention accuracy=1.
- hybrid / missing: n=1; recall=None; fact recall=None; abstention accuracy=0.
- hybrid / quality: n=3; recall=1.0; fact recall=1.0; abstention accuracy=1.
- hybrid / sre: n=2; recall=1.0; fact recall=1.0; abstention accuracy=1.

## Interpretation and limits

Closed-world manually adjudicated exact claim identity; unknown claims conservatively receive zero support/correctness and are counted. Not a general factuality verifier. Null metrics excluded from macro means; empty claims have undefined precision/support; unanswerable cases have undefined retrieval metrics unless conflict qrels exist.

Sequential warmed serial queries; retrieval includes tokenization/query embedding/fusion, excludes index build; pipeline adds evidence selection and extractive generation, excludes evaluation and report I/O. P95 nearest rank; each query repeated; method order fixed (thermal/order confounder).

Index build: 5875.011 ms. Peak process RSS: 552247296 bytes (whole process high-water mark, not per-method incremental memory). No API charges; CPU/energy opportunity cost is not zero and is not priced here.

The baseline copies up to two current retrieved chunks. It can cite irrelevant material perfectly, miss required facts, ignore active contradictions, and fail to abstain. Controlled fixtures test scoring independently from retrieval. Same-corpus development results are not held-out generalization evidence. No local generative LLM is required or measured.

For alternative chunk sizes, qrels remain atomic passage-level labels. Siblings are collapsed before K; any returned fragment counts as retrieving that passage (optimistic for fragmented evidence). Claim scoring remains exact authored text: split claims become unadjudicated, so chunk-sweep answer scores are not directly comparable without new human labels.

Hardware, versions, dataset hashes, configuration and UTC run times are recorded in metrics.json. Raw warmed latency samples are retained. See failure_analysis.md for observed failure classes.
