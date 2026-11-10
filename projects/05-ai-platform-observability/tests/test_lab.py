import asyncio
import json
from pathlib import Path
import httpx
import pytest
from prometheus_client import generate_latest
from ai_observability.app import create_app, CASES, SCENARIOS
from ai_observability.quality import evaluate
from ai_observability.slo import percentile, budget, objectives, alerts
from ai_observability.benchmark import run

def call(app, scenario='healthy', sequence=0, **kwargs):
    async def go():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://lab') as c:
            return await c.post('/query',json=dict(scenario=scenario,sequence=sequence,**kwargs),headers={'x-lab-key':'demo-a'})
    return asyncio.run(go())

@pytest.mark.parametrize('scenario',list(SCENARIOS))
def test_failures(scenario):
    app=create_app(); r=call(app,scenario).json()
    assert r['status']==(503 if scenario in ('timeout','mixed_incident') else 200)
    assert r['cost']==pytest.approx(sum(u['cost'] for u in r['usage']))
    assert r['fallback']==(scenario=='fallback')
    if scenario in ('unsupported','citation_degradation'):
        assert not r['quality']['passed']
    if scenario=='healthy': assert r['quality']['passed']
    assert r['stages']['end_to_end']>=r['stages']['provider']

@pytest.mark.parametrize('case,expected',[(k,k in ('supported','abstention')) for k in CASES])
def test_reference_labels(case,expected):
    assert evaluate(CASES[case])['passed']==expected

def test_specific_quality_signals():
    assert not evaluate(CASES['incorrect'])['correct']
    assert evaluate(CASES['unsupported'])['correct']
    assert not evaluate(CASES['unsupported'])['grounded']
    assert not evaluate(CASES['wrong_citation'])['citation']
    assert not evaluate(CASES['contradictory'])['grounded']
    assert not evaluate(CASES['stale'])['grounded']

def test_tracing_and_redaction(caplog):
    app=create_app()
    caplog.set_level('INFO',logger='ai.safe')
    async def go():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://lab') as c:
            return await c.post('/query',json={'scenario':'fallback','prompt':'SENSITIVE_SENTINEL'},headers={
               'x-lab-key':'demo-a','traceparent':'00-12345678901234567890123456789012-1234567890123456-01'})
    response=asyncio.run(go()); spans=app.state.telemetry.exporter.spans
    root=next(s for s in spans if s['name']=='inbound_request')
    assert root['trace_id']=='12345678901234567890123456789012'
    assert root['parent_id']=='1234567890123456'
    ids={s['span_id'] for s in spans}
    assert all(s['parent_id'] in ids for s in spans if s!=root)
    assert all(s['trace_id']==root['trace_id'] for s in spans)
    assert {'retry','fallback','provider_call','retrieval','answer_evaluation','cost_reconciliation'}<={s['name'] for s in spans}
    assert response.headers['traceparent'].split('-')[1]==root['trace_id']
    assert 'SENSITIVE_SENTINEL' not in json.dumps(spans)+caplog.text+json.dumps(app.state.store.records('tenant-a'))
    assert 'demo-a' not in caplog.text

def test_tenant_isolation_and_validation():
    app=create_app(); call(app)
    assert call(app,tenant='tenant-b').status_code==403
    async def go():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://lab') as c:
            assert (await c.get('/records',headers={'x-lab-key':'demo-b'})).json()==[]
            assert (await c.get('/records')).status_code==401
            assert len((await c.get('/records',headers={'x-lab-key':'demo-a'})).json())==1
            assert (await c.post('/query',json={'prompt':1},headers={'x-lab-key':'demo-a'})).status_code==422
    asyncio.run(go())

def test_cost_and_metrics():
    app=create_app(); r=call(app,'fallback').json()
    assert r['estimated_cost']==pytest.approx(.00016)
    assert r['cost']==pytest.approx(.00084)
    assert r['retries']==1 and len(r['usage'])==3
    metrics=generate_latest(app.state.telemetry.registry).decode()
    assert 'ai_requests_total{failure_category="none",status="200"} 1.0' in metrics
    assert 'ai_fallbacks_total 1.0' in metrics
    for forbidden in ('tenant-a','trace_id','request_id','prompt'):
        assert forbidden not in metrics

def test_percentiles():
    assert percentile([4,1,3,2],.5)==2
    assert percentile(list(range(100)),.95)==94
    assert percentile(list(range(100)),.99)==98
    assert percentile([], .5)==0
    with pytest.raises(ValueError): percentile([1],0)

def test_slo_denominators_and_budget():
    rows=[dict(status=200,latency=.01,quality={'passed':False},cost=.0001),
          dict(status=503,latency=.1,quality=None,cost=.002),dict(status=429)]
    s=objectives(rows)
    assert s['availability']['good']==1 and s['availability']['total']==2
    assert s['quality']['good']==0 and s['quality']['total']==1
    assert s['latency']['good']==1 and s['cost']['good']==1
    assert budget(98,100,.99)['consumption']==pytest.approx(2)
    assert budget(98,100,.99)['remaining']==pytest.approx(-1)
    assert budget(0,0,.99)['sli'] is None

def test_burn_alerts():
    healthy=[{'minute':i,'bad':False} for i in range(1,361)]
    assert not alerts(healthy,360)['page']
    incident=[{'minute':i,'bad':i>300} for i in range(1,361)]
    assert alerts(incident,360)['page']
    assert alerts(incident,360)['ticket']
    burst=[{'minute':i,'bad':i>355} for i in range(1,361)]
    assert not alerts(burst,360)['page'] # short window alone insufficient

def test_deterministic_decisions():
    a=call(create_app(),'retry_amplification').json(); b=call(create_app(),'retry_amplification').json()
    for k in ('status','quality','cost','usage','retries','fallback'): assert a[k]==b[k]

def test_report_generation(tmp_path):
    report=asyncio.run(run('quick',tmp_path))
    assert report['aggregate']['requests']==80
    assert report['aggregate']['transport_success']==68
    assert len(report['offline_quality'])==8
    for name in ('metrics.json','benchmark_report.md','slo_report.md','scenario_comparison.csv','cost_analysis.csv','failure_analysis.md','dashboard.html','traces-run-0.json'):
        assert (tmp_path/name).stat().st_size>0
    assert 'SENSITIVE_SENTINEL' not in (tmp_path/'metrics.json').read_text()

def test_stream():
    app=create_app()
    async def go():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://lab') as c:
            response=await c.post('/stream',json={},headers={'x-lab-key':'demo-a'})
            assert response.status_code==200
            lines=response.text.splitlines()
            assert len(lines)==2
            assert json.loads(lines[0])['simulated_ttft_seconds']>=.01
    asyncio.run(go())

def test_durable_store_and_no_payload(tmp_path):
    from ai_observability.storage import Store
    db=str(tmp_path/'records.sqlite')
    app=create_app(db)
    response=call(app,prompt='PRIVATE_INPUT_MARKER')
    assert response.json()['answer']=='retention=30'
    app.state.store.close()
    reopened=Store(db)
    rows=reopened.records('tenant-a')
    assert len(rows)==1 and rows[0]['trace_id']==response.json()['trace_id']
    assert 'PRIVATE_INPUT_MARKER' not in json.dumps(rows)
    assert 'answer' not in rows[0]
    assert reopened.records('tenant-b')==[]
    reopened.close()

def test_concurrency_queue_and_export_file(tmp_path):
    path=tmp_path/'spans.jsonl'; app=create_app(trace_path=str(path),concurrency=1)
    async def go():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://lab') as c:
            return await asyncio.gather(*(c.post('/query',json={'scenario':'latency_spike'},headers={'x-lab-key':'demo-a'}) for _ in range(2)))
    responses=asyncio.run(go())
    assert max(r.json()['stages']['queue'] for r in responses)>.05
    spans=[json.loads(line) for line in path.read_text().splitlines()]
    assert len([s for s in spans if s['name']=='inbound_request'])==2
    assert all(s['duration_ms']>=0 for s in spans)

def test_metric_observation_counts():
    app=create_app(); call(app,'timeout'); call(app,'unsupported')
    families={family.name:family for family in app.state.telemetry.registry.collect()}
    requests=[s for s in families['ai_requests'].samples if s.name=='ai_requests_total']
    assert sum(s.value for s in requests)==2
    attempts=[s for s in families['ai_provider_attempts'].samples if s.name=='ai_provider_attempts_total']
    assert sum(s.value for s in attempts)==4
    duration=[s for s in families['ai_stage_seconds'].samples if s.name=='ai_stage_seconds_count' and s.labels['stage']=='end_to_end']
    assert sum(s.value for s in duration)==2

def test_burn_window_boundary():
    from ai_observability.slo import burn
    assert burn([{'minute':55,'bad':True},{'minute':60,'bad':False}],60,5)==0
    assert burn([],60,5)==0
    with pytest.raises(ValueError): budget(2,1,.99)


def test_rate_limit_rejection_and_denominator():
    app=create_app(tenant_rpm=1)
    assert call(app).status_code==200
    rejected=call(app)
    assert rejected.status_code==429 and 'traceparent' in rejected.headers
    assert len(app.state.store.records('tenant-a'))==1
    metrics=generate_latest(app.state.telemetry.registry).decode()
    assert 'ai_admission_attempts_total 2.0' in metrics
    assert 'ai_rate_limit_rejections_total 1.0' in metrics
    assert 'tenant-a' not in metrics
