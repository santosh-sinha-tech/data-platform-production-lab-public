import json
import os
import subprocess
import sys
import threading
import httpx
import pytest
from pydantic import ValidationError
from agent_lab.engine import Engine
from agent_lab.models import (
    Action,
    Args,
    Request,
    Denied,
    Conflict,
    NotFound,
    EDGES,
    Interrupted,
)
from agent_lab.experiments import (
    Clock,
    OP,
    APPROVER,
    BETA,
    READER,
    SCENARIOS,
    custom,
    scenario,
    percentile,
    policy_cases,
)
from agent_lab.policy import authorize
from agent_lab.tools import TOOLS
from agent_lab.state import redact


@pytest.fixture
def engine(tmp_path):
    return Engine(tmp_path / "test.db", clock=Clock(), sleep=lambda _: None)


@pytest.mark.parametrize("old", list(EDGES))
@pytest.mark.parametrize("target", list(EDGES))
def test_state_transitions(engine, old, target):
    row = engine.submit(OP, custom("state", "read_quality"))
    engine.db.execute("UPDATE executions SET status=? WHERE id=?", (old, row["id"]))
    if target in EDGES[old]:
        engine.store.transition(row["id"], target)
    else:
        with pytest.raises(Conflict):
            engine.store.transition(row["id"], target)


@pytest.mark.parametrize("code,label,expected", SCENARIOS)
def test_scenarios(tmp_path, code, label, expected):
    result = scenario(code, tmp_path / f"{code}.db")
    assert result["actual"] == expected


@pytest.mark.parametrize("tool", TOOLS)
def test_reader_permissions(engine, tool):
    actions = [Action(tool=tool)]
    if TOOLS[tool].permission == "read":
        authorize(READER, "alpha", actions[0], actions, engine.config)
    else:
        with pytest.raises(Denied):
            authorize(READER, "alpha", actions[0], actions, engine.config)


def test_tenant_isolation(engine):
    row = engine.submit(OP, Request(key="a", workflow="deploy"))
    for fn in (
        engine.row,
        engine.recover,
        engine.reconcile,
        engine.cancel,
        engine.audit_records,
    ):
        with pytest.raises(NotFound):
            fn(row["id"], BETA)
    with pytest.raises(NotFound):
        engine.approve(row["id"], BETA, "approved")
    with pytest.raises(NotFound):
        engine.compensate(row["id"], 0, BETA)


def test_approval_exact_binding(engine):
    row = engine.submit(OP, Request(key="a", workflow="deploy"))
    plan = json.loads(row["plan"])
    plan[1]["args"]["value"] = "changed"
    engine.db.execute(
        "UPDATE executions SET plan=? WHERE id=?", (json.dumps(plan), row["id"])
    )
    with pytest.raises(Conflict):
        engine.approve(row["id"], APPROVER, "approved")
    assert engine.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0


def test_expired_approval(engine):
    row = engine.submit(OP, Request(key="a", workflow="deploy"))
    engine.clock.advance(60)
    assert (
        engine.approve(row["id"], APPROVER, "approved")["error"] == "approval expired"
    )


def test_approval_roles(engine):
    row = engine.submit(OP, Request(key="a", workflow="deploy"))
    with pytest.raises(Denied):
        engine.approve(row["id"], OP, "approved")
    with pytest.raises(Denied):
        engine.approve(row["id"], READER, "approved")


def test_duplicate_side_effects(engine):
    request = Request(key="duplicate")
    original = engine.submit(OP, request)
    for _ in range(5):
        assert engine.submit(OP, request)["id"] == original["id"]
        engine.run(original["id"], OP)
    assert engine.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 2
    with pytest.raises(Conflict):
        engine.submit(OP, Request(key="duplicate", workflow="deploy"))


def test_concurrent_duplicate_requests(engine):
    rows = []

    def call():
        rows.append(engine.submit(OP, Request(key="concurrent")))

    threads = [threading.Thread(target=call) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(rows) == 8 and len({r["id"] for r in rows}) == 1
    assert engine.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 2


def test_retry_and_timeout(engine):
    row = engine.submit(OP, custom("retry", "read_quality", "transient"))
    assert row["status"] == "succeeded"
    assert (
        engine.db.execute(
            "SELECT attempts FROM steps WHERE execution=?", (row["id"],)
        ).fetchone()[0]
        == 2
    )
    row = engine.submit(OP, custom("timeout", "read_quality", "timeout"))
    assert row["status"] == "failed"
    assert (
        engine.db.execute(
            "SELECT attempts FROM steps WHERE execution=?", (row["id"],)
        ).fetchone()[0]
        == 3
    )


def test_unknown_not_retried(engine):
    row = engine.submit(OP, custom("unknown", "rerun_pipeline", "unknown"))
    row = engine.approve(row["id"], APPROVER, "approved")
    for _ in range(3):
        assert engine.recover(row["id"], OP)["status"] == "unknown"
    assert engine.db.execute("SELECT attempts FROM steps").fetchone()[0] == 1
    assert engine.reconcile(row["id"], OP)["status"] == "succeeded"
    assert engine.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1


def test_timeout_write_no_evidence(engine):
    row = engine.submit(OP, custom("unknown", "rerun_pipeline", "timeout"))
    row = engine.approve(row["id"], APPROVER, "approved")
    assert row["status"] == "unknown"
    with pytest.raises(Conflict):
        engine.reconcile(row["id"], OP)


def test_restart_idempotent(tmp_path):
    path = tmp_path / "restart.db"
    e = Engine(path)
    with pytest.raises(Interrupted):
        e.submit(OP, custom("crash", "create_ticket", "interrupt"))
    eid = e.db.execute("SELECT id FROM executions").fetchone()[0]
    e.store.close()
    e = Engine(path)
    assert e.recover(eid, OP)["status"] == "succeeded"
    assert e.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1


def test_actual_process_death(tmp_path):
    path = tmp_path / "kill.db"
    code = """
import os
from agent_lab.engine import Engine
from agent_lab.experiments import OP, custom
from agent_lab.models import Interrupted
engine=Engine(os.environ['LAB_TEST_DB'])
try: engine.submit(OP,custom('kill','create_ticket','interrupt'))
except Interrupted: os._exit(77)
"""
    proc = subprocess.run(
        [sys.executable, "-c", code],
        env={**os.environ, "LAB_TEST_DB": str(path)},
        check=False,
    )
    assert proc.returncode == 77
    e = Engine(path)
    eid = e.db.execute("SELECT id FROM executions").fetchone()[0]
    assert e.recover(eid, OP)["status"] == "succeeded"
    assert e.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1


def test_resume_reauthorizes(engine):
    row = engine.submit(OP, Request(key="role", workflow="deploy"))
    engine.db.execute("UPDATE executions SET role='reader' WHERE id=?", (row["id"],))
    assert engine.approve(row["id"], APPROVER, "approved")["error"] == "policy denial"
    assert engine.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0


def test_retry_reauthorizes(engine):
    # Owner is read on every run; current policy table changes are consulted each attempt.
    from agent_lab import policy

    saved = policy.PERMISSIONS["operator"]

    def revoke_policy(_):
        policy.PERMISSIONS["operator"] = {"read"}

    engine.sleep = revoke_policy
    try:
        row = engine.submit(OP, custom("revoke", "create_ticket", "transient"))
        assert row["error"] == "policy denial"
    finally:
        policy.PERMISSIONS["operator"] = saved


def test_compensation(engine):
    row = engine.submit(
        OP,
        Request(
            key="partial",
            workflow="custom",
            actions=[
                Action(tool="create_ticket"),
                Action(tool="read_quality", fault="permanent"),
            ],
        ),
    )
    engine.compensate(row["id"], 0, OP)
    engine.compensate(row["id"], 0, OP)
    assert engine.db.execute("SELECT compensated FROM effects").fetchone()[0] == 1
    with pytest.raises(Denied):
        engine.compensate(row["id"], 1, OP)
    pending = engine.submit(OP, Request(key="cancel", workflow="rerun"))
    engine.cancel(pending["id"], OP)
    with pytest.raises(Denied):
        engine.compensate(pending["id"], 1, OP)


def test_budgets_depth_combinations(engine):
    with pytest.raises(Denied):
        engine.submit(
            OP,
            Request(
                key="depth",
                workflow="custom",
                actions=[Action(tool="read_quality")] * 9,
            ),
        )
    with pytest.raises(Denied):
        engine.submit(
            OP,
            Request(
                key="combo",
                workflow="custom",
                actions=[
                    Action(tool="update_deployment"),
                    Action(tool="rerun_pipeline"),
                ],
            ),
        )
    engine.config["max_cost"] = 0.001
    with pytest.raises(Denied):
        engine.submit(OP, Request(key="cost"))


def test_deadline(engine):
    row = engine.submit(OP, Request(key="deadline", workflow="deploy"))
    engine.clock.advance(31)
    assert (
        engine.approve(row["id"], APPROVER, "approved")["error"] == "execution deadline"
    )


def test_malicious_output_redaction(engine):
    row = engine.submit(OP, custom("inject", "get_runbook", "malicious"))
    assert row["status"] == "succeeded"
    assert engine.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0
    audit = json.dumps(engine.audit_records(row["id"], OP))
    assert "[REDACTED]" in audit and "synthetic-private-value" not in audit
    assert "IGNORE POLICY" in audit  # inert content, never parsed into a plan
    assert "user@example.invalid" not in redact({"contact": "user@example.invalid"})


def test_strict_inputs():
    with pytest.raises(ValidationError):
        Args(resource="../../etc")
    with pytest.raises(ValidationError):
        Action(tool="read_quality", admin=True)
    with pytest.raises(ValidationError):
        Args(value=123)


def test_metric_math_and_policy():
    assert percentile([1, 2, 3, 4], 0.95) == 4
    assert percentile([1, 2, 3, 4], 0.5) == 2
    assert percentile([], 0.5) == 0
    assert all(c["pass"] for c in policy_cases())


def test_reproducibility(tmp_path):
    a = scenario("H", tmp_path / "one.db")
    b = scenario("H", tmp_path / "two.db")
    for key in ("actual", "effects", "attempts", "steps", "cost", "audit_events"):
        assert a[key] == b[key]


@pytest.mark.anyio
async def test_http_api(engine):
    from agent_lab.app import create_app

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(engine)), base_url="http://lab"
    ) as client:
        h = {"X-Lab-Identity": "alpha-operator"}
        response = await client.post(
            "/executions", headers=h, json={"key": "api", "workflow": "deploy"}
        )
        assert response.status_code == 200
        eid = response.json()["id"]
        assert (
            await client.post(
                f"/executions/{eid}/approve",
                headers={"X-Lab-Identity": "beta-approver"},
            )
        ).status_code == 404
        assert (
            await client.post(
                f"/executions/{eid}/approve",
                headers={"X-Lab-Identity": "alpha-approver"},
            )
        ).json()["status"] == "succeeded"
        assert (
            await client.get(f"/executions/{eid}/audit", headers=h)
        ).status_code == 200
        text = (await client.get("/metrics")).text
        assert "agent_duration_seconds" in text and eid not in text
        assert (
            await client.post(
                "/executions",
                headers={"X-Lab-Identity": "alpha-reader"},
                json={"key": "deny"},
            )
        ).status_code == 403
        assert (await client.get("/health")).status_code == 200


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_non_idempotent_restart(tmp_path):
    path = tmp_path / "non-idempotent.db"
    e = Engine(path)
    row = e.submit(OP, custom("interrupted", "rerun_pipeline", "interrupt"))
    with pytest.raises(Interrupted):
        e.approve(row["id"], APPROVER, "approved")
    e.store.close()
    e = Engine(path)
    assert e.recover(row["id"], OP)["status"] == "unknown"
    assert e.db.execute("SELECT attempts FROM steps").fetchone()[0] == 1
    assert e.reconcile(row["id"], OP)["status"] == "succeeded"
    assert e.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1


def test_invalid_write_receipt_is_uncertain(engine):
    row = engine.submit(OP, custom("invalid-write", "create_ticket", "invalid"))
    assert row["status"] == "unknown"
    assert engine.db.execute("SELECT attempts FROM steps").fetchone()[0] == 1
    assert engine.reconcile(row["id"], OP)["status"] == "succeeded"


def test_actual_otel_spans(engine):
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    row = engine.submit(OP, custom("traced", "read_quality"))
    spans = exporter.get_finished_spans()
    assert {s.name for s in spans} == {"workflow.execute", "tool.execute"}
    workflow = next(s for s in spans if s.name == "workflow.execute")
    tool = next(s for s in spans if s.name == "tool.execute")
    assert workflow.attributes["execution.id"] == row["id"]
    assert workflow.context.trace_id == tool.context.trace_id
    assert tool.parent.span_id == workflow.context.span_id
