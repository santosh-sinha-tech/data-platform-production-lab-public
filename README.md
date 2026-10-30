# Data Platform Production Lab

Production-oriented **reference implementations** exploring data platform reliability, DataOps, observability, and publication governance.

Each experiment makes a production failure mode visible, defines a control, and verifies the resulting platform behaviour. Workloads are **synthetic / illustrative**; these are not claims about customer systems or production deployments.

| Reference implementation | Production question |
| --- | --- |
| [01 — Green Pipeline, Bad Data](projects/01-green-pipeline-bad-data/) | When every job succeeds, is the resulting data actually ready to publish? |
| [02 — Small Files Performance Lab](projects/02-small-files-performance-lab/) | When does rewriting fragmented Parquet justify its compute cost? |
| [03 — Enterprise RAG Evaluation Lab](projects/03-enterprise-rag-evaluation-lab/) | How do retrieval relevance, answer correctness, and citation support differ? |

## License

This repository is licensed under the [MIT License](LICENSE).
