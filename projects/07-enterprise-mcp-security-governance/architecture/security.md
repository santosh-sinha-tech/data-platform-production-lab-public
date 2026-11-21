# Security model

## Trusted inputs

The process owner controls the registry, example policy, code, fixture principal selector and stdio launch profile. A local reviewer fixture is a separate principal and must share the requester's tenant. The target catalog establishes ownership. Schema validation rejects caller-added identity fields. Registry access requires an approved server, an allowed tool, a tool-specific role grant and a matching risk grant.

MCP provides initialization, tool metadata and request/response transport. The gateway computes a SHA-256 digest of the tool name, description and canonicalized JSON input schema, so reordered object keys are stable. Approval binds the digest, full registry record, requester identity, application, tenant, tool risk and exact arguments. Any binding change fails closed. Discovery rejects duplicate names for the requested tool and incomplete paginated results.

## Credential and output boundaries

An injected synthetic grant for a different audience is denied before dispatch. The gateway additionally checks tenant, exact tool and expiry, including expiry after discovery. No customer tokens exist in the fixture. No credential claims are forwarded to the server, so the server exercises neither token validation nor OAuth. Broad credential reuse would erase the audience restriction modeled by this check.

Tool responses cross a trust boundary. Only a constant allowed state from structured output can reach the caller. The injected text is discarded and the unsupported result is classified as quarantined. The follow-on action requested by the fixture is separately attempted with the original read principal and denied. This deterministic comparison does not evaluate an LLM's susceptibility to prompt injection.

## Write execution and audit

The SQLite store atomically consumes a validated approval, reserves the caller's stable operation ID under tenant/server/tool scope and writes dispatch evidence. Each write tool records a synthetic side effect in its effects ledger. Neither timeout nor an MCP error after dispatch proves the write failed. The gateway keeps the reservation and marks the write outcome unknown. A crash before finalization can leave an in-flight reservation. Use a stable business intent ID across retries. A fresh ID can represent a new action and requires the appropriate authorization.

The audit schema uses known identities, known tool names, digests, decisions and generated correlations. Raw arguments, prompt content, tool payloads, approval identifiers and credential claims are excluded. The audit database is a local fixture and remains under host control.

## Residual risks

The gateway trusts the local host, configured fixture identities and the policy file. The stdio server uses the same OS account. A process that controls the local account can read or alter fixtures. Self-reported server metadata does not authenticate the process. A server may retain the same definition while changing its behavior, or change between list and call. PostgreSQL, durable shared budgets, authentication, production-grade sandboxing, output-size limits, signed policy, tamper-evident audit export and server-side exact-once effect handling remain deployment work.
