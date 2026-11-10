import argparse
import asyncio
import csv
import io
import json
import platform
import random
import statistics
import time
from pathlib import Path
import httpx
from .app import create_app, SCENARIOS, CASES
from .quality import evaluate
from .slo import percentile, objectives, alerts

VIEWS={
 'Executive AI Platform Health':['transport_success','quality_failure_rate','cost'],
 'Reliability and SLOs':['error_rate','slo'],
 'Latency and Throughput':['p50','p95','p99','throughput'],
 'Model and Provider Performance':['attempts','provider_p95'],
 'Answer Quality':['offline_quality','quality_failure_rate'],
 'Token Usage and Cost':['input_tokens','output_tokens','cost'],
 'Incident Investigation':['scenarios','trace_examples']}

def csv_text(rows):
    if not rows:
        return ''
    stream=io.StringIO(); writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
    return stream.getvalue()

def summary(rows, elapsed):
    success=[r for r in rows if r['status']==200]
    return dict(requests=len(rows),transport_success=len(success),error_rate=1-len(success)/len(rows),
        quality_failure_rate=sum(not r['quality']['passed'] for r in success)/len(success) if success else None,
        p50=percentile([r['latency'] for r in rows],.5),p95=percentile([r['latency'] for r in rows],.95),
        p99=percentile([r['latency'] for r in rows],.99),throughput=len(rows)/elapsed,
        client_p50=percentile([r.get('client_latency',r['latency']) for r in rows],.5),
        client_p95=percentile([r.get('client_latency',r['latency']) for r in rows],.95),
        client_p99=percentile([r.get('client_latency',r['latency']) for r in rows],.99),
        provider_p95=percentile([r['stages']['provider'] for r in rows],.95),
        retries=sum(r['retries'] for r in rows),attempts=sum(len(r['usage']) for r in rows),
        retry_amplification=sum(len(r['usage']) for r in rows)/len(rows),
        fallbacks=sum(r['fallback'] for r in rows),cost=sum(r['cost'] for r in rows),
        input_tokens=sum(u['input_tokens'] for r in rows for u in r['usage']),
        output_tokens=sum(u['output_tokens'] for r in rows for u in r['usage']),slo=objectives(rows))

async def run(mode: str, output: Path):
    output.mkdir(parents=True,exist_ok=True)
    runs=2 if mode=='quick' else 3; per_scenario=4 if mode=='quick' else 30; concurrency=4
    all_rows=[]; experiments=[]; comparisons=[]; traces=[]; stream_ttft=[]
    for run_index in range(runs):
        app=create_app(concurrency=concurrency)
        transport=httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport,base_url='http://lab') as client:
            await client.post('/query',json={},headers={'x-lab-key':'demo-a'}) # excluded warm-up
            run_rows=[]; wall=0.0
            for scenario in SCENARIOS:
                order=list(range(per_scenario)); random.Random(500+run_index).shuffle(order)
                gate=asyncio.Semaphore(concurrency)
                async def request(i):
                    tenant='tenant-b' if scenario=='tenant_cost_spike' else ('tenant-a' if i%2==0 else 'tenant-b')
                    async with gate:
                        client_start=time.perf_counter()
                        response=await client.post('/query',json=dict(scenario=scenario,sequence=i,tenant=tenant,
                            application='support' if i%2==0 else 'search'),headers={'x-lab-key':'demo-a' if tenant=='tenant-a' else 'demo-b'})
                        record=response.json()
                        record.pop('answer',None); record.pop('citation',None)
                        record['client_latency']=time.perf_counter()-client_start
                        return record
                start=time.perf_counter(); rows=await asyncio.gather(*(request(i) for i in order)); elapsed=time.perf_counter()-start
                wall+=elapsed; run_rows.extend(rows)
                s=summary(rows,elapsed)
                comparisons.append(dict(run=run_index,scenario=scenario,**{k:v for k,v in s.items() if k!='slo'}))
                traces.append(dict(scenario=scenario,run=run_index,request_id=rows[0]['request_id'],trace_id=rows[0]['trace_id']))
            stream=await client.post('/stream',json={},headers={'x-lab-key':'demo-a'})
            stream_ttft.append(json.loads(stream.text.splitlines()[0])['simulated_ttft_seconds'])
            metrics=(await client.get('/metrics')).text
        (output/f'prometheus-run-{run_index}.txt').write_text(metrics)
        # Intentional small, redacted trace evidence, excludes raw request content.
        selected={t['trace_id'] for t in traces if t['run']==run_index}
        span_rows=[s for s in app.state.telemetry.exporter.spans if s['trace_id'] in selected]
        (output/f'traces-run-{run_index}.json').write_text(json.dumps(span_rows,indent=2)+'\n')
        experiments.append(summary(run_rows,wall)); all_rows.extend(run_rows); app.state.store.close()
    offline=[dict(case=c['id'],**evaluate(c)) for c in CASES.values()]
    # One event/minute, aligned trailing windows. Incident lasts final 60 minutes.
    events=[dict(minute=m,bad=m>300) for m in range(1,361)]
    burn_incident=alerts(events,360)
    recovery_events=events+[dict(minute=m,bad=False) for m in range(361,721)]
    burn_recovery=alerts(recovery_events,720)
    aggregate=summary(all_rows,sum(len(all_rows)/runs/r['throughput'] for r in experiments))
    report=dict(mode=mode,runs=runs,per_scenario_per_run=per_scenario,seed_base=500,concurrency=concurrency,
       environment=dict(python=platform.python_version(),os=platform.system(),machine=platform.machine()),
       experiments=experiments,aggregate=aggregate,offline_quality=offline,offline_signal_rates={k:sum(row[k] for row in offline)/len(offline) for k in ('correct','grounded','citation','abstention','passed')},
       offline_appropriate_abstention_rate=sum(evaluate(c)['abstention'] for c in CASES.values() if c['should_abstain'])/sum(c['should_abstain'] for c in CASES.values()),
       online_sampling=dict(strategy='sequence modulo 5; deterministic synthetic sampling, not representative',eligible=sum(r['status']==200 and r['sequence']%5==0 for r in all_rows),failures=sum(r['status']==200 and r['sequence']%5==0 and not r['quality']['passed'] for r in all_rows)),
       attempt_cost_impact=dict(extra_attempt_cost=sum(sum(u['cost'] for u in r['usage'][1:]) for r in all_rows),fallback_cost=sum(u['cost'] for r in all_rows for u in r['usage'] if u['model']=='fallback'),estimate_total=sum(r['estimated_cost'] for r in all_rows)),trace_examples=traces,
       simulated_ttft_seconds=stream_ttft,burn_incident=burn_incident,burn_recovery=burn_recovery,
       variability={k:dict(mean=statistics.mean(r[k] for r in experiments),
                          stdev=statistics.stdev(r[k] for r in experiments)) for k in ('throughput','p95','p99')})
    (output/'metrics.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'scenario_comparison.csv').write_text(csv_text(comparisons))
    costs=[]
    for dimension in ('tenant','application','model','request','successful_request'):
        groups={}
        for r in all_rows:
            if dimension=='successful_request' and r['status']!=200:
                continue
            if dimension=='model':
                for u in r['usage']:
                    g=groups.setdefault(u['model'],dict(cost=0.,input_tokens=0,output_tokens=0,requests=set()))
                    for k in ('cost','input_tokens','output_tokens'): g[k]+=u[k]
                    g['requests'].add(r['request_id'])
            else:
                key=r[dimension] if dimension in ('tenant','application') else r['request_id']
                g=groups.setdefault(key,dict(cost=0.,input_tokens=0,output_tokens=0,requests=set()))
                g['cost']+=r['cost']; g['input_tokens']+=sum(u['input_tokens'] for u in r['usage']); g['output_tokens']+=sum(u['output_tokens'] for u in r['usage']); g['requests'].add(r['request_id'])
        for key,g in groups.items():
            costs.append(dict(dimension=dimension,key=key,requests=len(g['requests']),cost=g['cost'],
                             cost_per_request=g['cost']/len(g['requests']),input_tokens=g['input_tokens'],output_tokens=g['output_tokens']))
    (output/'cost_analysis.csv').write_text(csv_text(costs))
    text=['# Executed synthetic provider benchmark',f'Mode: {mode}; runs: {runs}; requests: {len(all_rows)}; concurrency: {concurrency}.',
          'Measured with HTTPX ASGI transport in one Python process. No network or commercial model performance claims.',
          'Each run has one excluded warm-up, then ten equally sized scenarios in lifecycle order. Seed shuffles sequence IDs within each scenario. Provider delays are in config/scenarios.json.',
          'Client p50/p95/p99 measure the full HTTPX ASGI round trip including parsing and middleware, without a real network. Other latency is application execution time including semaphore wait, excluding HTTP parsing and middleware. Throughput uses measured client batch wall time. Nearest-rank percentiles; aggregate percentiles pool observations.',
          '```json',json.dumps(aggregate,indent=2),'```','## Independent-run variability','```json',json.dumps(report['variability'],indent=2),'```',
          '## Environment','```json',json.dumps(report['environment'],indent=2),'```',
          '## Offline labeled quality',csv_text(offline),
          '## Simulated streaming',f'First scheduled token emission seconds: {stream_ttft}. ASGI buffers the stream; this is not client-observed TTFT.',
          '## Constraints','Wall times vary with scheduler and host load. Fixture decisions, attempt counts, and costs are deterministic; IDs and timing are intentionally variable. Small samples do not establish production tail latency.']
    (output/'benchmark_report.md').write_text('\n\n'.join(text)+'\n')
    (output/'slo_report.md').write_text('# Executed SLO report\n\nSee architecture SLO definitions. Window is this complete experiment; traffic is synthetic.\n\n```json\n'+json.dumps(dict(objectives=aggregate['slo'],incident=burn_incident,recovery=burn_recovery),indent=2)+'\n```\n')
    responses={'healthy':'Observe baseline.','latency_spike':'Inspect provider spans; reduce admission or route after cost review.',
      'timeout':'Inspect timeout attempts; avoid unlimited retries.','retry_amplification':'Reduce retry budget; compare attempt cost.',
      'fallback':'Assess latency and cost before routing more traffic.','unsupported':'Hold answer delivery and repair evidence policy.',
      'citation_degradation':'Validate citations before response.','tenant_cost_spike':'Investigate tenant records; enforce a production quota.',
      'mixed_incident':'Correlate quality with availability; roll back the offending change.','recovery':'Check trailing windows before resolving incident.'}
    lines=['# Executed failure analysis','Every row is measured synthetic traffic. Triggers are exact configuration values. Warm-up is excluded. No automatic production remediation is implemented.']
    for scenario,cfg in SCENARIOS.items():
        subset=[r for r in all_rows if r['scenario']==scenario]
        expected={'timeout':'503 after three timed-out billed attempts','mixed_incident':'even sequence 503; odd sequence 200 with quality failure',
                  'unsupported':'200 with quality failure','citation_degradation':'200 with quality failure',
                  'fallback':'200 on third attempt using higher-priced fallback','retry_amplification':'200 after two timeouts',
                  'tenant_cost_spike':'higher primary input usage attributed to tenant-b','latency_spike':'200 with provider latency above 80 ms',
                  'recovery':'healthy decisions resume; historical budget consumption remains','healthy':'200 with supported answer'}[scenario]
        lines.extend([f'## {scenario}',f'Trigger: `{json.dumps(cfg)}`. Expected: {expected}.',
                      'Measured outcomes and changed metrics:\n```json\n'+json.dumps({k:v for k,v in summary(subset,1).items() if k!='throughput'},indent=2)+'\n```',
                      'Measured scenario throughput is in scenario_comparison.csv.',
                      f'Trace: `{next(t for t in traces if t["scenario"]==scenario)["trace_id"]}` in traces-run-0.json.',
                      'Operational response: '+responses[scenario]])
    (output/'failure_analysis.md').write_text('\n\n'.join(lines)+'\n')
    # Equivalent locally rendered telemetry views, all values originate from this execution.
    html=['<!doctype html><meta charset="utf-8"><title>AI observability measured reports</title><style>body{font:16px system-ui;max-width:1100px;margin:2em auto}pre{white-space:pre-wrap;background:#eef;padding:1em}</style><h1>Local synthetic telemetry</h1>']
    values=dict(aggregate,offline_quality=offline,scenarios=comparisons,trace_examples=traces)
    for title,keys in VIEWS.items():
        html.append('<h2>'+title+'</h2><pre>'+json.dumps({k:values[k] for k in keys},indent=2)+'</pre>')
    (output/'dashboard.html').write_text('\n'.join(html))
    return report

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--mode',choices=['quick','full'],default='quick'); parser.add_argument('--output',type=Path,default=Path('results')); args=parser.parse_args()
    report=asyncio.run(run(args.mode,args.output)); print(json.dumps(report['aggregate'],indent=2))
if __name__=='__main__':
    main()
