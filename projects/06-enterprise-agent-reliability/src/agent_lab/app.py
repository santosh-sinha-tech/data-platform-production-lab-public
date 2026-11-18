from pathlib import Path
from fastapi import FastAPI, Header, HTTPException, Response
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from .engine import Engine
from .models import Identity, Request, Denied, Conflict, NotFound

# Public local fixtures, not authentication suitable for network deployment.
IDENTITIES = {
    "alpha-operator": Identity(tenant="alpha", subject="operator-a", role="operator"),
    "alpha-reader": Identity(tenant="alpha", subject="reader-a", role="reader"),
    "alpha-approver": Identity(tenant="alpha", subject="approver-a", role="approver"),
    "beta-approver": Identity(tenant="beta", subject="approver-b", role="approver"),
}


def create_app(engine=None):
    if engine is None:
        Path("runtime").mkdir(exist_ok=True)
        engine = Engine("runtime/lab.db")
    app = FastAPI(title="Enterprise Agent Reliability Lab")

    def identity(key):
        if key not in IDENTITIES:
            raise HTTPException(401, "unknown demo identity")
        return IDENTITIES[key]

    def call(fn, *args):
        try:
            return fn(*args)
        except Denied as exc:
            engine.metric("admission", "policy_denial")
            engine.event("admission", "policy_denial", {"reason": str(exc)})
            engine.db.commit()
            raise HTTPException(403, str(exc)) from exc
        except NotFound as exc:
            raise HTTPException(404, str(exc)) from exc
        except Conflict as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/executions")
    def submit(body: Request, x_lab_identity: str = Header()):
        return call(engine.submit, identity(x_lab_identity), body)

    @app.get("/executions/{eid}")
    def get(eid: str, x_lab_identity: str = Header()):
        return call(engine.row, eid, identity(x_lab_identity))

    @app.post("/executions/{eid}/approve")
    def approve(eid: str, x_lab_identity: str = Header()):
        return call(engine.approve, eid, identity(x_lab_identity), "approved")

    @app.post("/executions/{eid}/reject")
    def reject(eid: str, x_lab_identity: str = Header()):
        return call(engine.approve, eid, identity(x_lab_identity), "rejected")

    @app.post("/executions/{eid}/recover")
    def recover(eid: str, x_lab_identity: str = Header()):
        return call(engine.recover, eid, identity(x_lab_identity))

    @app.post("/executions/{eid}/reconcile")
    def reconcile(eid: str, x_lab_identity: str = Header()):
        return call(engine.reconcile, eid, identity(x_lab_identity))

    @app.post("/executions/{eid}/cancel")
    def cancel(eid: str, x_lab_identity: str = Header()):
        return call(engine.cancel, eid, identity(x_lab_identity))

    @app.get("/executions/{eid}/audit")
    def audit(eid: str, x_lab_identity: str = Header()):
        return call(engine.audit_records, eid, identity(x_lab_identity))

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/metrics")
    def metrics():
        # Reconstruct from durable observations, so restart doesn't erase counters.
        registry = CollectorRegistry()
        counts = Counter(
            "agent_events",
            "Durable control events",
            ["event", "tool"],
            registry=registry,
        )
        latency = Histogram(
            "agent_duration_seconds",
            "Observed duration",
            ["kind", "tool"],
            registry=registry,
        )
        for r in engine.db.execute("SELECT name,tool,value FROM observations"):
            if r["name"] in {"tool_latency", "approval_wait"}:
                latency.labels(r["name"], r["tool"]).observe(r["value"])
            else:
                counts.labels(r["name"], r["tool"]).inc(r["value"])
        states = Gauge(
            "agent_workflows",
            "Durable workflow state population",
            ["state"],
            registry=registry,
        )
        for r in engine.db.execute(
            "SELECT status,COUNT(*) AS n FROM executions GROUP BY status"
        ):
            states.labels(r["status"]).set(r["n"])
        cost = Gauge(
            "agent_simulated_cost_units",
            "Planning and tool attempt cost; synthetic units",
            registry=registry,
        )
        cost.set(
            engine.db.execute(
                "SELECT COALESCE(SUM(cost),0) FROM executions"
            ).fetchone()[0]
        )
        return Response(
            generate_latest(registry), media_type="text/plain; version=0.0.4"
        )

    app.state.engine = engine
    return app


app = create_app()
