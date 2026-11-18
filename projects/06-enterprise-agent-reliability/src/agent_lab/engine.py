"""Serialized local executor with durable checkpoints and explicit uncertain state."""

import hashlib
import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable
from pydantic import ValidationError
from opentelemetry import trace
from .models import (
    Action,
    Identity,
    Request,
    Denied,
    Conflict,
    NotFound,
    Interrupted,
    Transient,
    Permanent,
    Unknown,
)
from .policy import authorize, digest, plan
from .state import Store, redact
from .config import config_path
from .tools import TOOLS, Output, invoke

# Multiple Engine objects in one process share the execution lock. Cross-process
# workers are deliberately unsupported: see architecture deployment boundary.
LOCK = threading.RLock()
TRACER = trace.get_tracer("agent-lab")


class Engine:
    def __init__(
        self,
        path: str | Path,
        config: dict[str, Any] | None = None,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.store = Store(str(path))
        self.db = self.store.db
        defaults = config_path("example.yaml")
        self.config = json.loads(defaults.read_text())
        if config:
            self.config.update(config)
        self.clock, self.sleep = clock, sleep

    def row(self, eid: str, identity: Identity) -> dict[str, Any]:
        row = self.db.execute("SELECT * FROM executions WHERE id=?", (eid,)).fetchone()
        if row is None or row["tenant"] != identity.tenant:
            raise NotFound("execution not found")
        return dict(row)

    def event(self, eid: str, kind: str, detail: dict[str, Any] | None = None) -> None:
        self.store.audit(eid, self.clock(), kind, detail)

    def metric(
        self, eid: str, name: str, value: float = 1, tool: str = "workflow"
    ) -> None:
        self.store.observe(eid, name, value, tool)

    def fail(self, eid: str, reason: str) -> None:
        self.store.transition(eid, "failed")
        self.db.execute("UPDATE executions SET error=? WHERE id=?", (reason, eid))
        self.event(eid, "failed", {"reason": reason})
        self.metric(eid, "completion", 0)
        self.db.commit()

    def submit(self, identity: Identity, request: Request) -> dict[str, Any]:
        with LOCK:
            rh = hashlib.sha256(request.model_dump_json().encode()).hexdigest()
            prior = self.db.execute(
                "SELECT * FROM executions WHERE tenant=? AND request_key=?",
                (identity.tenant, request.key),
            ).fetchone()
            if prior:
                if prior["request_hash"] != rh:
                    raise Conflict("idempotency key reused with different request")
                self.metric(prior["id"], "duplicate")
                self.db.commit()
                return self.row(prior["id"], identity)
            actions = plan(request)
            if not actions:
                raise Denied("empty plan")
            # Whole-plan validation occurs before any effects.
            for action in actions:
                authorize(identity, identity.tenant, action, actions, self.config)
            estimated = (
                self.config["prices"]["planning"]
                + len(actions) * self.config["prices"]["tool"]
            )
            if estimated > self.config["max_cost"]:
                raise Denied("estimated cost budget")
            eid = str(uuid.uuid4())
            now = self.clock()
            self.db.execute(
                "INSERT INTO executions(id,tenant,subject,role,request_key,request_hash,plan,status,cost,deadline,created) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    eid,
                    identity.tenant,
                    identity.subject,
                    identity.role,
                    request.key,
                    rh,
                    json.dumps([a.model_dump() for a in actions]),
                    "created",
                    self.config["prices"]["planning"],
                    now + self.config["deadline_seconds"],
                    now,
                ),
            )
            self.db.executemany(
                "INSERT INTO steps(execution,idx,status) VALUES (?,?,?)",
                [(eid, i, "pending") for i in range(len(actions))],
            )
            self.event(eid, "created", {"steps": len(actions)})
            self.store.transition(eid, "running")
            self.db.commit()
            return self.run(eid, identity)

    def run(self, eid: str, identity: Identity) -> dict[str, Any]:
        with (
            LOCK,
            TRACER.start_as_current_span(
                "workflow.execute", attributes={"execution.id": eid}
            ),
        ):
            row = self.row(eid, identity)
            if row["status"] != "running":
                return row
            actions = [Action.model_validate(a) for a in json.loads(row["plan"])]
            # Execution owner role persists; caller cannot elevate a resumed workflow.
            owner = Identity(
                tenant=row["tenant"], subject=row["subject"], role=row["role"]
            )
            for idx in range(row["cursor"], len(actions)):
                action = actions[idx]
                tool = TOOLS.get(action.tool)
                while True:
                    row = self.row(eid, identity)
                    step = self.db.execute(
                        "SELECT * FROM steps WHERE execution=? AND idx=?", (eid, idx)
                    ).fetchone()
                    if self.clock() >= row["deadline"]:
                        self.fail(eid, "execution deadline")
                        return self.row(eid, identity)
                    try:
                        authorize(owner, row["tenant"], action, actions, self.config)
                    except (Denied, ValidationError):
                        self.metric(eid, "policy_denial")
                        self.fail(eid, "policy denial")
                        return self.row(eid, identity)
                    if tool.approval:
                        approval = self.db.execute(
                            "SELECT * FROM approvals WHERE execution=? AND idx=?",
                            (eid, idx),
                        ).fetchone()
                        if approval is None or approval["digest"] != digest(action):
                            self.db.execute(
                                "INSERT OR REPLACE INTO approvals VALUES (?,?,?,?,?,?,?,?)",
                                (
                                    eid,
                                    idx,
                                    digest(action),
                                    self.clock() + self.config["approval_ttl"],
                                    "pending",
                                    None,
                                    self.clock(),
                                    None,
                                ),
                            )
                            self.store.transition(eid, "pending_approval")
                            self.event(
                                eid,
                                "approval_requested",
                                {"step": idx, "digest": digest(action)},
                            )
                            self.db.commit()
                            return self.row(eid, identity)
                        if approval["expires"] <= self.clock():
                            self.fail(eid, "approval expired")
                            return self.row(eid, identity)
                        if approval["decision"] != "approved":
                            self.fail(eid, "approval not granted")
                            return self.row(eid, identity)
                    # A crash after checkpoint but before receipt leaves this state.
                    if step["status"] == "executing" and not tool.idempotent:
                        self.store.transition(eid, "unknown")
                        self.event(eid, "unknown", {"step": idx})
                        self.db.commit()
                        return self.row(eid, identity)
                    if step["attempts"] >= self.config["max_retries"] + 1:
                        self.fail(eid, "retry limit")
                        return self.row(eid, identity)
                    price = self.config["prices"]["tool"]
                    if row["cost"] + price > self.config["max_cost"]:
                        self.fail(eid, "execution cost budget")
                        return self.row(eid, identity)
                    attempt = step["attempts"] + 1
                    self.db.execute(
                        "UPDATE steps SET status='executing',attempts=? WHERE execution=? AND idx=?",
                        (attempt, eid, idx),
                    )
                    self.db.execute(
                        "UPDATE executions SET cost=cost+? WHERE id=?", (price, eid)
                    )
                    self.event(
                        eid,
                        "attempt",
                        {"step": idx, "tool": action.tool, "attempt": attempt},
                    )
                    self.db.commit()
                    started = time.perf_counter()
                    try:
                        with TRACER.start_as_current_span(
                            "tool.execute", attributes={"tool.name": action.tool}
                        ):
                            output = Output.model_validate(
                                invoke(
                                    self.db,
                                    row["tenant"],
                                    f"{eid}:{idx}",
                                    action,
                                    attempt,
                                )
                            )
                    except Interrupted:
                        self.event(eid, "process_interruption", {"step": idx})
                        self.db.commit()
                        raise
                    except Unknown:
                        self.store.transition(eid, "unknown")
                        self.event(eid, "unknown", {"step": idx})
                        self.metric(eid, "step_failure", tool=action.tool)
                        self.db.commit()
                        return self.row(eid, identity)
                    except (Transient, Permanent, ValidationError) as exc:
                        self.metric(eid, "step_failure", tool=action.tool)
                        self.event(
                            eid,
                            "step_failure",
                            {"step": idx, "type": type(exc).__name__},
                        )
                        if isinstance(exc, ValidationError) and tool.risk != "read":
                            self.store.transition(eid, "unknown")
                            self.event(
                                eid,
                                "unknown",
                                {"step": idx, "reason": "invalid write receipt"},
                            )
                            self.db.commit()
                            return self.row(eid, identity)
                        self.db.execute(
                            "UPDATE steps SET status='pending' WHERE execution=? AND idx=?",
                            (eid, idx),
                        )
                        if (
                            isinstance(exc, Transient)
                            and tool.retry_safe
                            and tool.idempotent
                            and attempt <= self.config["max_retries"]
                        ):
                            self.metric(eid, "retry", tool=action.tool)
                            self.db.commit()
                            self.sleep(
                                self.config["backoff_seconds"] * 2 ** (attempt - 1)
                            )
                            continue
                        self.fail(eid, "tool failure: " + type(exc).__name__)
                        return self.row(eid, identity)
                    finally:
                        self.metric(
                            eid,
                            "tool_latency",
                            time.perf_counter() - started,
                            action.tool,
                        )
                        self.db.commit()
                    self.db.execute(
                        "UPDATE steps SET status='succeeded',output=? WHERE execution=? AND idx=?",
                        (redact(output.model_dump()), eid, idx),
                    )
                    self.db.execute(
                        "UPDATE executions SET cursor=? WHERE id=?", (idx + 1, eid)
                    )
                    self.event(
                        eid,
                        "step_succeeded",
                        {"step": idx, "output": output.model_dump()},
                    )
                    self.db.commit()
                    break
            self.store.transition(eid, "succeeded")
            self.metric(eid, "completion", 1)
            self.event(eid, "succeeded")
            self.db.commit()
            return self.row(eid, identity)

    def approve(self, eid: str, identity: Identity, decision: str) -> dict[str, Any]:
        with LOCK:
            if decision not in {"approved", "rejected"}:
                raise Conflict("invalid approval decision")
            row = self.row(eid, identity)
            if identity.role != "approver" or identity.subject == row["subject"]:
                raise Denied("independent approver required")
            if row["status"] != "pending_approval":
                raise Conflict("not awaiting approval")
            idx = row["cursor"]
            approval = self.db.execute(
                "SELECT * FROM approvals WHERE execution=? AND idx=?", (eid, idx)
            ).fetchone()
            action = Action.model_validate(json.loads(row["plan"])[idx])
            if approval["digest"] != digest(action):
                raise Conflict("action changed; request new approval")
            if self.clock() >= approval["expires"]:
                self.metric(eid, "approval_wait", self.clock() - approval["requested"])
                self.event(eid, "approval_expired")
                self.fail(eid, "approval expired")
                return self.row(eid, identity)
            self.db.execute(
                "UPDATE approvals SET decision=?,approver=?,decided=? WHERE execution=? AND idx=?",
                (decision, identity.subject, self.clock(), eid, idx),
            )
            self.metric(eid, "approval_wait", self.clock() - approval["requested"])
            self.event(
                eid,
                "approval_" + decision,
                {"approver": identity.subject, "digest": approval["digest"]},
            )
            if decision == "rejected":
                self.fail(eid, "approval rejected")
                return self.row(eid, identity)
            self.store.transition(eid, "running")
            self.db.commit()
            return self.run(eid, identity)

    def recover(self, eid: str, identity: Identity) -> dict[str, Any]:
        with LOCK:
            row = self.row(eid, identity)
            if identity.role != "operator" and identity.subject != row["subject"]:
                raise Denied("operator or execution owner required for recovery")
            self.event(eid, "recovery_requested")
            if row["status"] == "pending_approval":
                ap = self.db.execute(
                    "SELECT expires,requested FROM approvals WHERE execution=? AND idx=?",
                    (eid, row["cursor"]),
                ).fetchone()
                if self.clock() >= ap[0]:
                    self.metric(eid, "approval_wait", self.clock() - ap[1])
                    self.event(eid, "approval_expired")
                    self.fail(eid, "approval expired")
                self.db.commit()
                return self.row(eid, identity)
            result = self.run(eid, identity)
            self.metric(eid, "recovery", int(result["status"] == "succeeded"))
            self.db.commit()
            return result

    def reconcile(self, eid: str, identity: Identity) -> dict[str, Any]:
        with LOCK:
            row = self.row(eid, identity)
            if identity.role != "operator":
                raise Denied("operator required")
            if row["status"] != "unknown":
                raise Conflict("not uncertain")
            idx = row["cursor"]
            # Trusted simulator ledger is the evidence, never caller assertion.
            effect = self.db.execute(
                "SELECT output FROM effects WHERE tenant=? AND step_key=?",
                (row["tenant"], f"{eid}:{idx}"),
            ).fetchone()
            if effect is None:
                raise Conflict("no completion evidence; manual investigation required")
            actions = [Action.model_validate(a) for a in json.loads(row["plan"])]
            owner = Identity(
                tenant=row["tenant"], subject=row["subject"], role=row["role"]
            )
            authorize(owner, row["tenant"], actions[idx], actions, self.config)
            self.db.execute(
                "UPDATE steps SET status='succeeded',output=? WHERE execution=? AND idx=?",
                (redact({"content": effect[0]}), eid, idx),
            )
            self.db.execute("UPDATE executions SET cursor=? WHERE id=?", (idx + 1, eid))
            self.event(eid, "reconciled", {"step": idx, "evidence": "simulator ledger"})
            self.store.transition(eid, "running")
            self.db.commit()
            result = self.run(eid, identity)
            self.metric(eid, "recovery", int(result["status"] == "succeeded"))
            self.db.commit()
            return result

    def cancel(self, eid: str, identity: Identity) -> dict[str, Any]:
        with LOCK:
            self.row(eid, identity)
            if identity.role != "operator":
                raise Denied("operator required")
            self.store.transition(eid, "cancelled")
            self.event(eid, "cancelled")
            self.db.commit()
            return self.row(eid, identity)

    def compensate(self, eid: str, idx: int, identity: Identity) -> None:
        with LOCK:
            row = self.row(eid, identity)
            if identity.role != "operator" or row["status"] not in {
                "failed",
                "cancelled",
            }:
                raise Denied("terminal failed/cancelled operator workflow required")
            actions = [Action.model_validate(a) for a in json.loads(row["plan"])]
            if idx < 0 or idx >= len(actions):
                raise Conflict("invalid step")
            action = actions[idx]
            authorize(identity, row["tenant"], action, actions, self.config)
            if not TOOLS[action.tool].reversible or TOOLS[action.tool].approval:
                raise Denied("compensation not preauthorized")
            self.db.execute(
                "UPDATE effects SET compensated=1 WHERE tenant=? AND step_key=?",
                (row["tenant"], f"{eid}:{idx}"),
            )
            self.event(eid, "compensated", {"step": idx})
            self.db.commit()

    def audit_records(self, eid: str, identity: Identity) -> list[dict[str, Any]]:
        self.row(eid, identity)
        return [
            dict(r)
            for r in self.db.execute(
                "SELECT * FROM audit WHERE execution=? ORDER BY seq", (eid,)
            )
        ]
