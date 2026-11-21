import asyncio
import json
import sqlite3

import pytest
from pydantic import ValidationError

from mcp_governance.gateway import Denied
from mcp_governance.metrics import latency, summarize
from mcp_governance.policy import Credential, Policy, load_policy
from mcp_governance.scenarios import LABELS, ROOT, TARGET, open_gateway, run_case
from mcp_governance.transport import connect


@pytest.mark.parametrize("case", LABELS)
def test_scenario(case, tmp_path):
    first = asyncio.run(run_case(case, tmp_path / "first.sqlite"))
    second = asyncio.run(run_case(case, tmp_path / "second.sqlite"))
    assert first["passed"] and second["passed"]
    stable = {"outcome", "authorization", "approval", "audit_outcomes", "effects", "recovery"}
    assert {key: first[key] for key in stable} == {key: second[key] for key in stable}


def test_registry_rejects_invalid_tool():
    data = load_policy(ROOT / "config/policy.json").model_dump()
    data["servers"]["operations"]["tools"].append("missing-tool")
    with pytest.raises(ValidationError):
        Policy.model_validate(data)


def test_protocol_server_version_and_tool_output(tmp_path):
    async def check():
        gateway = open_gateway(tmp_path / "gateway.sqlite")
        async with connect(ROOT, gateway.store.ledger) as connection:
            initialized, _ = connection
            assert initialized.protocolVersion == "2025-11-25"
            result = await gateway.execute("reader", "operations", "pipeline_status", TARGET,
                                           connection=connection)
            assert (result.outcome, result.state) == ("ok", "healthy")
            gateway.policy.servers["operations"] = gateway.policy.servers["operations"].model_copy(
                update={"version": 2}
            )
            result = await gateway.execute("reader", "operations", "pipeline_status", TARGET,
                                           connection=connection)
            assert result.outcome == "server_changed"
    asyncio.run(check())


def test_approval_binding_and_argument_redaction(tmp_path):
    async def check():
        gateway = open_gateway(tmp_path / "gateway.sqlite")
        args = {**TARGET, "mode": "active"}
        params = ("operator", "operations", "change_config")
        with pytest.raises(Denied, match="unauthorized_approver"):
            gateway.approve("other_reviewer", *params, args)
        approval = gateway.approve("reviewer", *params, args)
        async with connect(ROOT, gateway.store.ledger) as connection:
            async def invoke(arguments):
                return await gateway.execute(*params, arguments, connection=connection,
                                             approval=approval, operation_id="private-intent-fixture")
            assert (await invoke({**args, "tenant": "never-log-this"})).outcome == "invalid_arguments"
            assert (await invoke({**args, "mode": "paused"})).outcome == "approval_binding"
            assert (await invoke(args)).outcome == "ok"
        events = json.dumps(gateway.store.events())
        for excluded in ("never-log-this", "private-intent-fixture", "alpha/orders", approval):
            # Approval issuance has its own audit correlation, independent of the grant ID.
            assert excluded not in events
    asyncio.run(check())


def test_credential_scope_and_capacity(tmp_path):
    async def check():
        gateway = open_gateway(tmp_path / "gateway.sqlite", budget=0, clock=lambda: 1000)
        params = ("reader", "operations", "pipeline_status", TARGET)
        scoped = Credential(audience="operations", tenant="alpha", tool="pipeline_status",
                            expires=1000)
        assert (await gateway.execute(*params, credential=scoped)).outcome == "credential_scope"
        assert (await gateway.execute(*params)).outcome == "capacity"
    asyncio.run(check())


def test_atomic_cross_gateway_intent(tmp_path):
    async def check():
        db = tmp_path / "gateway.sqlite"
        first, second = open_gateway(db), open_gateway(db)
        params = ("operator", "operations", "rerun_pipeline", TARGET)
        async with connect(ROOT, first.store.ledger) as connection:
            async def execute(gateway):
                approval = gateway.approve("reviewer", *params)
                return await gateway.execute(*params, operation_id="shared-operation",
                                             connection=connection, approval=approval)
            results = await asyncio.gather(execute(first), execute(second))
        assert sorted(result.outcome for result in results) == ["duplicate", "ok"]
        assert first.store.effect_count() == 1
        with sqlite3.connect(db) as connection:
            assert connection.execute("SELECT status FROM operation").fetchone() == ("ok",)
    asyncio.run(check())


def test_metrics_nearest_rank_and_denominator():
    assert latency([None]) == {"n": 0}
    assert latency(range(1, 101))["p95"] == 95
    assert latency([9, 1, None, 3])["p50"] == 3
    rows = [
        dict(case="E", outcome="definition_drift", passed=True, audit_complete=True,
             recovery="not_applicable", approval_wait_ms=None),
        dict(case="K", outcome="timeout", passed=True, audit_complete=True,
             recovery="ok", approval_wait_ms=None),
    ]
    result = summarize(rows)
    assert result["policy_denial_rate"] == .5
    assert result["drift_detected"] == result["drift_trials"] == 1
    assert result["recovery"] == {"ok": 1}
