import asyncio
import json
import logging
import os
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from .quality import evaluate
from .storage import Store
from .telemetry import Telemetry

LOGGER=logging.getLogger('ai.safe')
LOGGER.setLevel(logging.INFO)
if not LOGGER.handlers:
    handler=logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    LOGGER.addHandler(handler)

ROOT=Path(__file__).resolve().parents[2]
SCENARIOS=json.loads((ROOT/'config/scenarios.json').read_text())
CASES={c['id']:c for c in json.loads((ROOT/'config/quality.json').read_text())}
PRICES=json.loads((ROOT/'config/prices.json').read_text())

class Query(BaseModel):
    model_config=ConfigDict(extra='forbid')
    tenant: Literal['tenant-a','tenant-b']='tenant-a'
    application: Literal['support','search']='support'
    scenario: str='healthy'
    prompt: str=Field(default='synthetic request',max_length=1000)
    sequence: int=Field(default=0,ge=0)

def create_app(db: str=':memory:', trace_path: str | None=None, concurrency: int=4, tenant_rpm: int=10000) -> FastAPI:
    app=FastAPI(title='Enterprise AI Observability Lab')
    store=Store(db); telemetry=Telemetry(trace_path); semaphore=asyncio.Semaphore(concurrency)
    app.state.store=store; app.state.telemetry=telemetry
    # Deliberately local demo identities, not production authentication.
    identities={'demo-a':'tenant-a','demo-b':'tenant-b'}
    if tenant_rpm<1:
        raise ValueError('tenant_rpm must be positive')
    quota: dict[str, tuple[int,int]]={}
    def identity(key):
        tenant=identities.get(key)
        if tenant is None:
            raise HTTPException(401,'local demo identity required')
        return tenant

    @app.middleware('http')
    async def inbound(request: Request, call_next):
        if request.url.path not in ('/query','/stream'):
            return await call_next(request)
        context=TraceContextTextMapPropagator().extract(dict(request.headers))
        with telemetry.tracer.start_as_current_span('inbound_request',context=context) as span:
            request.state.request_id=uuid.uuid4().hex
            request.state.trace_id=f'{span.get_span_context().trace_id:032x}'
            response=await call_next(request)
            span.set_attribute('http.response.status_code',response.status_code)
            span.set_status(Status(StatusCode.ERROR if response.status_code>=400 else StatusCode.OK))
            response.headers['x-request-id']=request.state.request_id
            TraceContextTextMapPropagator().inject(response.headers)
            # No payload, identity header or exception text is logged.
            LOGGER.info(json.dumps(dict(request_id=request.state.request_id,
                      trace_id=request.state.trace_id,status=response.status_code)))
            return response

    async def execute(q: Query, request: Request, key: str | None):
        start=time.perf_counter(); stages={}; usage=[]; retries=0; fallback=False
        @contextmanager
        def stage(name):
            with telemetry.tracer.start_as_current_span(name,record_exception=False,set_status_on_exception=False) as span:
                try:
                    yield span
                except Exception:
                    span.set_status(Status(StatusCode.ERROR))
                    raise
                else:
                    if span.status.status_code!=StatusCode.ERROR:
                        span.set_status(Status(StatusCode.OK))
        with stage('request_validation'):
            tenant=identity(key)
            if tenant!=q.tenant:
                raise HTTPException(403,'tenant mismatch')
            if q.scenario not in SCENARIOS:
                raise HTTPException(422,'unknown scenario')
            cfg=SCENARIOS[q.scenario]
            telemetry.admissions.inc()
            minute=int(time.monotonic()//60)
            previous,count=quota.get(tenant,(minute,0))
            count=count if previous==minute else 0
            if count>=tenant_rpm:
                telemetry.rejections.inc()
                raise HTTPException(429,'local tenant request quota exceeded')
            # No await between checking and incrementing: atomic within this one event loop.
            quota[tenant]=(minute,count+1)
        queue=time.perf_counter()
        async with semaphore:
            stages['queue']=time.perf_counter()-queue
            with stage('retrieval'):
                t=time.perf_counter(); await asyncio.sleep(.002); stages['retrieval']=time.perf_counter()-t
            with stage('model_selection'):
                model='primary'
            timeouts=3 if cfg.get('mixed') and q.sequence%2==0 else cfg.get('timeouts',0)
            status=503; provider_time=0.0
            for attempt in range(3):
                if attempt:
                    if cfg.get('fallback') and attempt==2:
                        model='fallback'; fallback=True; telemetry.fallbacks.inc()
                        wrapper='fallback'
                    else:
                        retries+=1; telemetry.retries.inc(); wrapper='retry'
                else:
                    wrapper='initial_attempt'
                with stage(wrapper):
                    with stage('provider_call') as span:
                        t=time.perf_counter(); await asyncio.sleep(cfg['delay']*(1.5 if model=='fallback' else 1))
                        elapsed=time.perf_counter()-t; provider_time+=elapsed
                        failed=attempt<timeouts and model!='fallback'
                        span.set_attribute('model.profile',model)
                        span.set_attribute('attempt',attempt+1)
                        span.set_attribute('failure.category','timeout' if failed else 'none')
                        if failed:
                            span.set_status(Status(StatusCode.ERROR))
                        tokens=cfg.get('tokens',100); output=0 if failed else 30
                        prices=PRICES[model]
                        cost=(tokens*prices['input_per_million']+output*prices['output_per_million'])/1e6
                        usage.append(dict(model=model,provider='simulated',input_tokens=tokens,output_tokens=output,
                                          cost=cost,timeout=failed))
                        telemetry.attempts.labels(model,'timeout' if failed else 'success').inc()
                        telemetry.cost.labels(model).inc(cost)
                if not failed:
                    status=200; break
            stages['provider']=provider_time
            quality=None
            if status==200:
                with stage('answer_evaluation'):
                    t=time.perf_counter(); quality=evaluate(CASES[cfg['case']]); stages['evaluation']=time.perf_counter()-t
                    if not quality['passed']:
                        telemetry.degraded.inc()
            with stage('cost_reconciliation'):
                cost=sum(u['cost'] for u in usage)
                estimated=(cfg.get('tokens',100)*PRICES['primary']['input_per_million']+30*PRICES['primary']['output_per_million'])/1e6
        latency=time.perf_counter()-start
        stages['application_overhead']=max(0,latency-sum(stages.values()))
        stages['end_to_end']=latency
        for name,value in stages.items():
            telemetry.duration.labels('/query',name).observe(value)
        category='none' if status==200 else 'provider_timeout'
        telemetry.requests.labels(str(status),category).inc()
        record=dict(request_id=request.state.request_id,trace_id=request.state.trace_id,tenant=tenant,
                    application=q.application,scenario=q.scenario,status=status,failure_category=category,
                    latency=latency,stages=stages,quality=quality,usage=usage,cost=cost,estimated_cost=estimated,
                    retries=retries,fallback=fallback,sequence=q.sequence)
        store.save(record)
        return record

    @app.post('/query')
    async def query(q: Query, request: Request, x_lab_key: str | None=Header(default=None)):
        record=await execute(q,request,x_lab_key)
        with telemetry.tracer.start_as_current_span('response',record_exception=False) as span:
            span.set_status(Status(StatusCode.OK))
            payload=dict(record)
            if record['status']==200:
                case=CASES[SCENARIOS[q.scenario]['case']]
                payload['answer']=case['claim'] if not case['abstained'] else 'Insufficient evidence'
                payload['citation']=case['citation']
            return JSONResponse(payload,status_code=record['status'])

    @app.post('/stream')
    async def stream(q: Query, request: Request, x_lab_key: str | None=Header(default=None)):
        identity(x_lab_key)
        if identity(x_lab_key)!=q.tenant:
            raise HTTPException(403,'tenant mismatch')
        # Explicit simulation: TTFT is scheduled emission, not client/network receipt.
        async def tokens():
            t=time.perf_counter()
            with telemetry.tracer.start_as_current_span('simulated_stream',record_exception=False):
                await asyncio.sleep(.01)
                ttft=time.perf_counter()-t
                telemetry.duration.labels('/stream','simulated_ttft').observe(ttft)
                yield json.dumps({'token':'synthetic','simulated_ttft_seconds':ttft})+'\n'
                await asyncio.sleep(.002)
                yield json.dumps({'token':'done'})+'\n'
        return StreamingResponse(tokens(),media_type='application/x-ndjson')

    @app.get('/records')
    def records(x_lab_key: str | None=Header(default=None)):
        return store.records(identity(x_lab_key))

    @app.get('/metrics')
    def metrics():
        return Response(generate_latest(telemetry.registry),media_type=CONTENT_TYPE_LATEST)

    @app.get('/health')
    def health():
        return {'status':'ok','provider':'synthetic'}
    return app

app=create_app(os.getenv('LAB_DB',':memory:'),os.getenv('LAB_TRACE_PATH'),tenant_rpm=int(os.getenv('LAB_TENANT_RPM','120')))
