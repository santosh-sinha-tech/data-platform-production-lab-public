# Santosh Sinha Tech

Engineering portfolio of production-oriented reference implementations for data platforms, reliability, observability, and AI evaluation.

## Data Platform Production Lab

The default `main` branch is the portfolio of completed reference labs; feature branches are used for development and review.

Each project explores a distinct production engineering question. All projects sit alongside one another under `projects/`, with their own implementation, documentation, tests, and measured evidence.

```text
Santosh Sinha Tech
└── Data Platform Production Lab
    └── projects/
        ├── 01-green-pipeline-bad-data/
        ├── 02-small-files-performance-lab/
        ├── 03-enterprise-rag-evaluation-lab/
        ├── 04-enterprise-llm-gateway/
        ├── 05-ai-platform-observability/
        ├── 06-enterprise-agent-reliability/
        └── 07-enterprise-mcp-security-governance/
```

| Project | Production question | Start here |
| --- | --- | --- |
| **01 — Green Pipeline, Bad Data** | When every job succeeds, is the resulting data actually ready to publish? | [Project 01](projects/01-green-pipeline-bad-data/README.md) |
| **02 — Small Files Performance Lab** | When does rewriting fragmented Parquet justify its compute cost? | [Project 02](projects/02-small-files-performance-lab/README.md) |
| **03 — Enterprise RAG Evaluation Lab** | How do retrieval relevance, answer correctness, and citation support differ? | [Project 03](projects/03-enterprise-rag-evaluation-lab/README.md) |
| **04 — Enterprise LLM Gateway** | How can an AI platform enforce model access, reliable execution and accountable simulated spend? | [Project 04](projects/04-enterprise-llm-gateway/README.md) |
| **05 — AI Platform Observability** | How can operational signals distinguish transport success from useful AI outcomes? | [Project 05](projects/05-ai-platform-observability/README.md) |
| **06 — Enterprise Agent Reliability & Governance** | Can an agent execute the correct tool safely under failure, approval and policy constraints? | [Project 06](projects/06-enterprise-agent-reliability/README.md) |
| **07 — Enterprise MCP Security & Governance** | Who decides whether a discovered MCP tool is safe and authorized to execute? | [Project 07](projects/07-enterprise-mcp-security-governance/README.md) |

Workloads are synthetic and illustrative. Results describe the recorded experiments, not customer systems or production deployments. Each project's documentation records its verification outcomes, limitations, and any outstanding checks.

## Security and privacy

Every current and future project follows the [public repository security and privacy policy](SECURITY.md). It requires staged-file review, synthetic-data and privacy checks, author metadata review, appropriate dependency checks, and dedicated secret scanning before publication. Native or Docker-based Gitleaks can be used; scans must cover all unpublished commits, including inherited changes.

See the [project audit index](docs/security-audits/README.md) for recorded evidence and limitations, and the [audit report template](docs/security-audit-template.md) for each new project. Missing required checks keep publication on HOLD. No scan guarantees the absence of every possible leak, and publication still requires explicit owner authorization.

## License

This repository is licensed under the [MIT License](LICENSE).
