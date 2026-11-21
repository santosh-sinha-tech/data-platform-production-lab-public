"""Labeled fixtures exercising the same gateway and MCP adapter as the benchmark."""

import asyncio
import time
from contextlib import AsyncExitStack
from dataclasses import asdict
from pathlib import Path

from .gateway import Gateway
from .policy import Credential, load_policy
from .store import Store
from .transport import connect

ROOT = Path(__file__).resolve().parents[2]
TARGET = {"target": "alpha/orders"}
LABELS = {
    "A": ("approved and authorized", "ok", 0),
    "B": ("unapproved server", "unapproved_server", 0),
    "C": ("unauthorized tool", "unauthorized_tool", 0),
    "D": ("cross-tenant target", "tenant_mismatch", 0),
    "E": ("schema change after approval", "definition_drift", 0),
    "F": ("description manipulation", "definition_drift", 0),
    "G": ("untrusted tool output", "quarantined", 0),
    "H": ("credential audience mismatch", "credential_audience", 0),
    "I": ("expired approval", "approval_expired", 0),
    "J": ("approval replay", "approval_replay", 1),
    "K": ("read deadline", "timeout", 0),
    "L": ("duplicate high-impact intent", "duplicate", 1),
    "M": ("server unavailable during initialization", "server_unavailable", 0),
    "N": ("committed effect with lost reply", "unknown", 1),
}


def open_gateway(path, **kwargs):
    return Gateway(load_policy(ROOT / "config/policy.json"), Store(path), **kwargs)


async def run_case(label, path):
    now = 1000.0
    gateway = open_gateway(path, clock=lambda: now)
    fixture, server, tool, arguments = "reader", "operations", "pipeline_status", TARGET
    options = {}
    if label == "B":
        server = "unreviewed"
    if label == "D":
        arguments = {"target": "beta/orders"}
    if label == "H":
        options["credential"] = Credential(audience="different_server", tenant="alpha",
                                           tool=tool, expires=1100)
    if label in "CEIJLN":
        tool = "rerun_pipeline"
    if label in "EIJLN":
        fixture = "operator"
        options["operation_id"] = "intent-001"
        options["approval"] = gateway.approve("reviewer", fixture, server, tool, arguments)
        now += 61 if label == "I" else 1

    variant = {"E": "schema", "F": "description", "G": "untrusted", "K": "slow",
               "M": "unavailable", "N": "lost_reply"}.get(label, "normal")
    setup = None
    recovery = "not_applicable"
    async with AsyncExitStack() as stack:
        connection = None
        if label not in "BCDH":
            try:
                connection = await stack.enter_async_context(
                    connect(ROOT, gateway.store.ledger, variant)
                )
            except Exception:
                if label != "M":
                    raise
            if label == "M" and connection is not None:
                raise AssertionError("unavailable fixture unexpectedly initialized")

        async def invoke():
            return await gateway.execute(fixture, server, tool, arguments,
                                         connection=connection, **options)

        if label in "JL":
            setup = (await invoke()).outcome
            if label == "L":
                options["approval"] = gateway.approve("reviewer", fixture, server, tool, arguments)
        result = await invoke()
        if label == "N":
            options["approval"] = gateway.approve("reviewer", fixture, server, tool, arguments)
            recovery = (await invoke()).outcome
        if label == "G":
            recovery = (await gateway.execute(fixture, server, "change_config",
                                              {**TARGET, "mode": "paused"},
                                              connection=connection)).outcome
        if label == "K":
            healthy = await stack.enter_async_context(connect(ROOT, gateway.store.ledger))
            recovery = (await gateway.execute(fixture, server, tool, arguments,
                                              connection=healthy)).outcome

    events = gateway.store.events()
    related = [event for event in events if event["correlation"] == result.correlation]
    description, expected, effects = LABELS[label]
    observed_effects = gateway.store.effect_count()
    required = {"correlation", "requester", "tenant", "application", "server", "tool",
                "definition", "authorization", "approval", "outcome"}
    complete = bool(related) and all(required <= event.keys() for event in related)
    expected_recovery = {"G": "unauthorized_tool", "K": "ok", "N": "duplicate"}
    passed = (
        result.outcome == expected and observed_effects == effects and complete
        and (label not in "JL" or setup == "ok")
        and recovery == expected_recovery.get(label, "not_applicable")
    )
    return {
        "case": label, "scenario": description, "expected": expected,
        **asdict(result), "authorization": related[-1]["authorization"] if related else None,
        "approval": related[-1]["approval"] if related else None,
        "audit_outcomes": "|".join(event["outcome"] for event in related),
        "audit_complete": complete, "effects": observed_effects, "recovery": recovery,
        "passed": passed,
    }


async def benchmark(path, count, concurrency):
    gateway = open_gateway(path, concurrency=concurrency, deadline=1, budget=count)
    samples = []
    async with connect(ROOT, gateway.store.ledger) as connection:
        async def call():
            return await gateway.execute("reader", "operations", "pipeline_status", TARGET,
                                         connection=connection)

        start = time.perf_counter()
        for offset in range(0, count, concurrency):
            batch = min(concurrency, count - offset)
            samples.extend(await asyncio.gather(*(call() for _ in range(batch))))
        elapsed = time.perf_counter() - start
    if any(sample.outcome != "ok" for sample in samples):
        raise AssertionError("benchmark encountered an unsuccessful call")
    return [asdict(sample) for sample in samples], elapsed
