# Executed verification

| Check | Result |
| --- | --- |
| Pinned SDK and actual SDK API | MCP Python SDK 1.30.0 imports and negotiates protocol 2025-11-25 over stdio |
| Environment consistency | `pip check` passed on Darwin arm64 Python 3.13.3 and Docker Python 3.11.14 |
| Native pytest | 20 passed, 0 failed, 0 skipped |
| Container compatibility pytest | 20 passed, 0 failed, 0 skipped |
| Quick experiment | 28/28 scenario trials and 80 successful measured calls |
| Full experiment | 42/42 scenario trials and 900 successful measured calls |
| Artifact verifier | Passed independently on both modes |
| Dependency vulnerability review | pip-audit 2.10.1 reported no known vulnerabilities for the final lock |
| Resource observation | macOS `time -l` could not read a kernel setting. Python `resource.getrusage` completed the separate quick observation. |
| Scope | No cloud dependencies, real accounts, production data or external tool targets exercised |

The first audit of the provisional pins reported advisories in MCP 1.26.0, pytest 9.0.2 and setuptools 80.9.0. These were replaced with 1.30.0, 9.0.3 and 84.1.0. Recorded tests and benchmarks use the patched versions. The first local run of the provisional stdio adapter passed a subprocess sentinel to `open()` and failed before initialization. The adapter now opens the OS null device by path.

Run the [README commands](../README.md) to reproduce the checks. Python 3.11 compatibility was tested in the existing Project 06 Linux container using a read-only project mount and a fresh virtual environment. The full benchmark was measured natively. External authentication, remote transports, process sandboxing and multi-host capacity are outside the verified lab scope.

See the [repository publication audit](../../../docs/security-audits/07-enterprise-mcp-security-governance.md) for staged and committed scope.
