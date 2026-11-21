"""Governance entry point for trusted local fixture identities."""

import asyncio
import math
import time
from dataclasses import dataclass
from uuid import uuid4

from jsonschema import Draft202012Validator

from .policy import PRINCIPALS, Credential, definition, fingerprint


@dataclass(frozen=True)
class Result:
    outcome: str
    correlation: str
    discovery_ms: float | None
    authorization_ms: float
    execution_ms: float | None
    total_ms: float
    approval_wait_ms: float | None
    state: str | None


class Denied(Exception):
    pass


class Gateway:
    def __init__(self, policy, store, *, deadline=0.15, concurrency=4, budget=10_000,
                 clock=time.time):
        self.policy = policy
        self.store = store
        self.deadline = deadline
        self.slots = asyncio.Semaphore(concurrency)
        self.budget = budget
        self.clock = clock

    def _check(self, fixture, server, name, arguments):
        principal = PRINCIPALS.get(fixture)
        record = self.policy.servers.get(server)
        if record is None or record.trust != "approved":
            raise Denied("unapproved_server")
        if principal is None:
            raise Denied("unknown_identity")
        tool = self.policy.tools.get(name)
        if (name not in record.tools or principal.role not in tool.roles
                or tool.risk not in self.policy.roles.get(principal.role, [])):
            raise Denied("unauthorized_tool")
        if not Draft202012Validator(tool.schema_).is_valid(arguments):
            raise Denied("invalid_arguments")
        if self.policy.targets.get(arguments["target"]) != principal.tenant:
            raise Denied("tenant_mismatch")
        version = definition(name, tool.description, tool.schema_)
        binding = fingerprint([principal.model_dump(), server, record.model_dump(), name,
                               version, tool.risk, arguments])
        return principal, record, tool, version, binding

    def approve(self, reviewer, fixture, server, name, arguments, *, ttl=60):
        principal, _, tool, version, binding = self._check(fixture, server, name, arguments)
        signer = PRINCIPALS.get(reviewer)
        if (signer is None or signer.role != "approver" or signer.tenant != principal.tenant
                or signer.subject == principal.subject or tool.risk != "high"):
            raise Denied("unauthorized_approver")
        if not math.isfinite(ttl) or not 0 < ttl <= 300:
            raise ValueError("approval TTL must be between zero and 300 seconds")
        now = self.clock()
        identifier = uuid4().hex
        self.store.approve(identifier, binding, now, now + ttl,
                           {**self._event(fixture, server, name, uuid4().hex),
                            "definition": version, "approver": signer.subject,
                            "authorization": "allowed", "approval": "approved"})
        return identifier

    def _event(self, fixture, server, name, correlation):
        principal = PRINCIPALS.get(fixture)
        return {
            "correlation": correlation,
            "requester": principal.subject if principal else "unknown",
            "tenant": principal.tenant if principal else None,
            "application": principal.application if principal else None,
            "server": server if server in self.policy.servers else "unknown",
            "tool": name if name in self.policy.tools else "unknown",
            "definition": None, "authorization": "denied", "approval": "not_evaluated",
        }

    async def execute(self, fixture, server, name, arguments, *, connection=None,
                      approval=None, operation_id=None, credential=None):
        started = time.perf_counter()
        correlation = uuid4().hex
        event = self._event(fixture, server, name, correlation)
        discovery_ms = execution_ms = approval_wait_ms = None
        authorization_ms = 0.0
        operation = state = None
        dispatched = False
        try:
            # Detach caller-owned input before awaiting anything.
            arguments = dict(arguments)
            principal, record, tool, version, binding = self._check(fixture, server, name, arguments)
            event.update(definition=version, registry_version=record.version)
            now = self.clock()
            if credential is None:
                credential = Credential(audience=server, tenant=principal.tenant,
                                        tool=name, expires=now + 60)
            if credential.audience != server:
                raise Denied("credential_audience")
            if (credential.tenant != principal.tenant or credential.tool != name
                    or not math.isfinite(credential.expires) or credential.expires <= now):
                raise Denied("credential_scope")
            event["authorization"] = "allowed"
            event["approval"] = "required" if tool.risk == "high" else "not_required"
            authorization_ms = (time.perf_counter() - started) * 1000
            if tool.risk == "high" and not approval:
                raise Denied("approval_required")
            if tool.risk != "read":
                if not isinstance(operation_id, str) or not 1 <= len(operation_id) <= 128:
                    raise Denied("operation_id_required")
                operation = fingerprint([principal.tenant, server, name, operation_id])
            if self.slots.locked() or self.budget <= 0:
                raise Denied("capacity")
            async with self.slots:
                self.budget -= 1
                if connection is None:
                    raise Denied("server_unavailable")
                initialized, session = connection
                peer = initialized.serverInfo
                if (peer.name, peer.version, initialized.protocolVersion) != (
                    server, str(record.version), self.policy.protocol
                ):
                    raise Denied("server_changed")
                discovery_start = time.perf_counter()
                try:
                    async with asyncio.timeout(self.deadline):
                        listing = await session.list_tools()
                except Exception:
                    raise Denied("discovery_failed") from None
                discovery_ms = (time.perf_counter() - discovery_start) * 1000
                matches = [item for item in listing.tools if item.name == name]
                if listing.nextCursor or len(matches) != 1:
                    raise Denied("tool_inventory")
                item = matches[0]
                if definition(item.name, item.description, item.inputSchema) != version:
                    raise Denied("definition_drift")
                now = self.clock()
                if credential.expires <= now:
                    raise Denied("credential_scope")
                if tool.risk == "high":
                    event["approval"] = "approved"
                decision, approval_wait_ms = self.store.start(
                    event, operation, approval if tool.risk == "high" else None, binding, now,
                )
                if decision != "dispatched":
                    if decision != "duplicate":
                        event["approval"] = decision
                    raise Denied(decision)
                dispatched = True
                execution_start = time.perf_counter()
                try:
                    async with asyncio.timeout(self.deadline):
                        response = await session.call_tool(name, arguments)
                    if response.isError:
                        outcome = "tool_error" if operation is None else "unknown"
                    else:
                        output = response.structuredContent or {}
                        permitted = "healthy" if tool.risk == "read" else "accepted"
                        state = permitted if output.get("state") == permitted else None
                        outcome = "ok" if set(output) == {"state"} and state else "quarantined"
                        if outcome == "quarantined":
                            state = None
                except asyncio.CancelledError:
                    self.store.finish(event, "cancelled" if operation is None else "unknown",
                                      operation)
                    raise
                except TimeoutError:
                    outcome = "timeout" if operation is None else "unknown"
                except Exception:
                    outcome = "transport_error" if operation is None else "unknown"
                finally:
                    execution_ms = (time.perf_counter() - execution_start) * 1000
        except Denied as error:
            outcome = str(error)
        if authorization_ms == 0.0:
            authorization_ms = (time.perf_counter() - started) * 1000
        self.store.finish(event, outcome, operation if dispatched else None)
        return Result(outcome, correlation, discovery_ms, authorization_ms, execution_ms,
                      (time.perf_counter() - started) * 1000, approval_wait_ms, state)
