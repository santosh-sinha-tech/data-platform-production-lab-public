import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from pathlib import Path
import yaml
from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, ConfigDict
from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest
from .store import Store, Denied
from .policy import cost, routes
from .providers import SimulatedProvider, ProviderError, Breaker


class Generation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    app: str = Field(min_length=1, max_length=32)
    prompt: str = Field(min_length=1, max_length=4096)
    capability: str = Field(default="basic", pattern="^(basic|quality)$")
    model: str | None = None
    input_tokens: int = Field(ge=1, le=16384)
    max_output_tokens: int = Field(default=32, ge=1, le=1024)
    timeout: float = Field(default=0.3, ge=0.01, le=2)
    cost_ceiling: int = Field(default=10000, ge=0)
    allow_fallback: bool = True


class Screening:
    """Replace with a reviewed PII/content service. Default performs no DLP."""

    def check(self, request):
        return None


def create_app(config=None, db=None, clock=time.time):
    config = config or yaml.safe_load(
        Path(os.getenv("GATEWAY_CONFIG", "config/example.yaml")).read_text()
    )
    store = Store(db or os.getenv("GATEWAY_DB", "gateway.db"))
    store.recover()
    app = FastAPI(title="Enterprise LLM Gateway — local simulator")
    app.state.store = store
    app.state.config = config
    registry = CollectorRegistry()
    counts = Counter("gateway_requests", "Requests", ["status"], registry=registry)
    events = Counter(
        "gateway_events", "Bounded control events", ["kind", "model"], registry=registry
    )
    tokens = Counter(
        "gateway_tokens", "Token accounting", ["kind", "model"], registry=registry
    )
    costs = Counter(
        "gateway_cost_micro_usd",
        "Simulated model charge",
        ["tenant", "app", "model"],
        registry=registry,
    )
    latency = Histogram(
        "gateway_latency_seconds", "Latency", ["stage"], registry=registry
    )
    provider = SimulatedProvider()
    app.state.provider = provider
    breakers = {
        m: Breaker(clock, lambda state, m=m: events.labels("circuit_" + state, m).inc())
        for m in config["models"]
    }
    app.state.breakers = breakers
    screening = Screening()
    logger = logging.getLogger("gateway")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)

    def auth(key):
        for tenant, policy in config["tenants"].items():
            if key == policy["key"]:
                return tenant, policy
        raise Denied("unauthenticated", 401)

    @app.middleware("http")
    async def observe(request: Request, call_next):
        try:
            rid = str(uuid.UUID(request.headers.get("X-Request-ID", "")))
        except ValueError:
            rid = str(uuid.uuid4())
        request.state.rid = rid
        start = clock()
        try:
            response = await call_next(request)
        except Exception:
            # The durable ledger retains uncertain dispatches. Never echo exception
            # details: provider errors can contain private request content.
            response = JSONResponse(
                status_code=500,
                content={"error": {"code": "internal_error", "request_id": rid}},
            )
        counts.labels(str(response.status_code)).inc()
        latency.labels("gateway_total").observe(clock() - start)
        response.headers["X-Request-ID"] = rid
        logging.getLogger("gateway").info(
            json.dumps(
                {
                    "request_id": rid,
                    "status": response.status_code,
                    "event": "request_complete",
                }
            )
        )
        return response

    @app.exception_handler(Denied)
    async def denied(request, exc):
        return JSONResponse(
            status_code=exc.status,
            content={"error": {"code": exc.code, "request_id": request.state.rid}},
            headers={"Retry-After": str(exc.retry)} if exc.retry else {},
        )

    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return JSONResponse(
            status_code=422,
            content={
                "error": {"code": "invalid_request", "request_id": request.state.rid}
            },
        )

    @app.get("/health")
    def health():
        return {"status": "ok", "deployment": "single-process-local"}

    @app.get("/metrics")
    def metrics():
        return Response(
            generate_latest(registry), media_type="text/plain; version=0.0.4"
        )

    @app.get("/v1/usage")
    def usage(x_api_key: str = Header(default="")):
        tenant, _ = auth(x_api_key)
        # No prompts, response text, idempotency keys, or fingerprints in metadata API.
        rows = []
        for r in store.records("requests", tenant):
            metadata = {
                k: r[k] for k in ("app", "period", "state", "reserved", "charged")
            }
            response = json.loads(r["response"]) if r["response"] else None
            if response:
                metadata.update(
                    model=response["model"],
                    actual_tokens=sum(response["usage"].values()),
                    estimated_tokens=response["estimated_tokens"],
                )
            rows.append(metadata)
        return rows

    @app.get("/v1/costs")
    def cost_report(x_api_key: str = Header(default="")):
        tenant, policy = auth(x_api_key)
        rows = [
            r
            for r in store.records("requests", tenant)
            if r["period"] == config["period"]
        ]
        apps = {
            a: {"charged": 0, "held": 0, "budget": policy["app_budget"]}
            for a in policy["apps"]
        }
        models = {}
        successes = 0
        delta = 0
        estimated = 0
        for row in rows:
            entry = apps.setdefault(
                row["app"], {"charged": 0, "held": 0, "budget": policy["app_budget"]}
            )
            entry["charged"] += row["charged"]
            if row["state"] in ("reserved", "unresolved"):
                entry["held"] += row["reserved"]
            result = json.loads(row["response"]) if row["response"] else None
            if result:
                model = result["model"]
                successes += 1
                estimated += result["estimated_cost_micro_usd"]
                delta += result["fallback_cost_delta_micro_usd"]
            else:
                model = "unattributed"
            models[model] = models.get(model, 0) + row["charged"]
        charged = sum(a["charged"] for a in apps.values())
        held = sum(a["held"] for a in apps.values())
        for a in apps.values():
            a["utilization"] = (
                (a["charged"] + a["held"]) / a["budget"] if a["budget"] else None
            )
        return {
            "tenant": tenant,
            "period": config["period"],
            "currency": "USD",
            "unit": "micro-USD",
            "simulated": True,
            "charged": charged,
            "held": held,
            "budget": policy["budget"],
            "utilization": (
                (charged + held) / policy["budget"] if policy["budget"] else None
            ),
            "by_application": apps,
            "by_model": models,
            "estimated_cost_completed": estimated,
            "fallback_delta": delta,
            "cost_per_success": charged / successes if successes else None,
        }

    @app.get("/v1/audit")
    def audit(x_api_key: str = Header(default="")):
        tenant, _ = auth(x_api_key)
        return store.records("audits", tenant)

    @app.post("/v1/generate")
    async def generate(
        body: Generation,
        request: Request,
        x_api_key: str = Header(default=""),
        idempotency_key: str = Header(min_length=1, max_length=128),
    ):
        tenant, policy = auth(x_api_key)
        rid = request.state.rid

        def reject(code, status=403, retry=None):
            store.audit(
                tenant,
                body.app if body.app in policy["apps"] else "[denied]",
                rid,
                code,
            )
            events.labels(code, "none").inc()
            raise Denied(code, status, retry)

        if body.app not in policy["apps"]:
            reject("app_forbidden")
        if len(body.prompt) > config.get("limits", {}).get("input_chars", 4096):
            reject("input_too_large", 422)
        if body.input_tokens < len(body.prompt.encode()):
            reject("input_underestimate", 422)
        screening.check(body)
        total = body.input_tokens + body.max_output_tokens
        models = config["models"]
        try:
            preferred, candidates, amount = routes(body, policy, models)
        except Denied as exc:
            reject(exc.code, exc.status)
        fingerprint = hashlib.sha256(body.model_dump_json().encode()).hexdigest()
        try:
            cached = store.reserve(
                tenant,
                body.app,
                idempotency_key,
                fingerprint,
                config["period"],
                amount,
                total,
                policy,
                int(clock() // 60),
            )
        except Denied as e:
            reject(e.code, e.status, e.retry)
        if cached is not None:
            store.audit(tenant, body.app, rid, "idempotent_replay")
            return cached
        tokens.labels("estimated", preferred).inc(total)
        store.audit(tenant, body.app, rid, "reserved")
        deadline = clock() + body.timeout
        dispatched = False
        try:
            for index, model in enumerate(candidates):
                if index:
                    events.labels("fallback", model).inc()
                profile = models[model]
                breaker = breakers[model]
                for attempt in range(2):
                    if clock() >= deadline:
                        raise ProviderError("deadline")
                    entered = False
                    try:
                        permit = breaker.enter()
                        entered = True
                        dispatched = True
                        started = clock()
                        try:
                            result = await asyncio.wait_for(
                                provider.generate(
                                    model, profile, body.prompt, body.max_output_tokens
                                ),
                                min(profile.get("timeout", 0.075), deadline - clock()),
                            )
                        finally:
                            latency.labels("provider_attempt").observe(
                                clock() - started
                            )
                        u = result["usage"]
                        if not u or not all(
                            type(u.get(k)) is int and 0 <= u[k] <= limit
                            for k, limit in [
                                ("input", body.input_tokens),
                                ("output", body.max_output_tokens),
                            ]
                        ):
                            raise ProviderError("unknown_usage", False)
                        breaker.result(True, permit)
                        charge = cost(u["input"] + u["output"], profile["price"])
                        response = {
                            "request_id": rid,
                            "model": model,
                            "text": result["text"],
                            "usage": u,
                            "estimated_tokens": total,
                            "reserved_micro_usd": amount,
                            "estimated_cost_micro_usd": cost(
                                total, models[preferred]["price"]
                            ),
                            "primary_model": preferred,
                            "fallback_cost_delta_micro_usd": charge
                            - cost(
                                u["input"] + u["output"], models[preferred]["price"]
                            ),
                            "cost_micro_usd": charge,
                            "currency": "USD",
                            "simulated": True,
                        }
                        store.finish(
                            tenant,
                            body.app,
                            idempotency_key,
                            "completed",
                            charge,
                            response,
                        )
                        tokens.labels("actual", model).inc(sum(u.values()))
                        costs.labels(tenant, body.app, model).inc(charge)
                        store.audit(tenant, body.app, rid, "completed")
                        return response
                    except (ProviderError, asyncio.TimeoutError) as exc:
                        kind = exc.kind if isinstance(exc, ProviderError) else "timeout"
                        events.labels("provider_" + kind, model).inc()
                        if entered:
                            breaker.result(False, permit)
                        if isinstance(exc, ProviderError) and not exc.safe:
                            raise
                        if kind == "timeout" and not provider.replay_safe:
                            raise ProviderError("unknown_completion", False)
                        if (
                            attempt == 0
                            and provider.replay_safe
                            and kind in ("429", "500", "intermittent", "timeout")
                        ):
                            events.labels("retry", model).inc()
                            await asyncio.sleep(0.001)
                        else:
                            break
            raise ProviderError("providers_exhausted")
        except asyncio.CancelledError:
            store.finish(
                tenant,
                body.app,
                idempotency_key,
                "unresolved" if dispatched else "released",
            )
            raise
        except ProviderError as exc:
            unresolved = not exc.safe
            store.finish(
                tenant,
                body.app,
                idempotency_key,
                "unresolved" if unresolved else "released",
            )
            reject("unknown_completion" if unresolved else exc.kind, 503)
        except BaseException:
            store.finish(tenant, body.app, idempotency_key, "unresolved")
            raise

    return app


app = create_app() if os.getenv("GATEWAY_SERVE") == "1" else None
