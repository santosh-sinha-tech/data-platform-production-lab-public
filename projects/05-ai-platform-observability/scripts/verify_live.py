"""Run from a container on the Compose network after generating local traffic."""
import argparse
import json
import time
from pathlib import Path
import httpx

parser=argparse.ArgumentParser()
parser.add_argument('--api',default='http://api:8000')
parser.add_argument('--stack',action='store_true')
parser.add_argument('--output',type=Path,default=Path('/runtime/live_verification.json'))
args=parser.parse_args()
checks={}
with httpx.Client(timeout=10) as client:
    checks['api_health']=client.get(args.api+'/health').json()['status']=='ok'
    for scenario in ('healthy','latency_spike','timeout','retry_amplification','fallback','unsupported',
                     'citation_degradation','tenant_cost_spike','mixed_incident','recovery'):
        tenant='tenant-b' if scenario=='tenant_cost_spike' else 'tenant-a'
        response=client.post(args.api+'/query',json={'scenario':scenario,'tenant':tenant},
                             headers={'x-lab-key':'demo-b' if tenant=='tenant-b' else 'demo-a'})
        data=response.json()
        checks[scenario]={'status':response.status_code,'cost':data['cost'],'trace_id':data['trace_id'],
                          'quality':data['quality']}
        assert response.status_code==(503 if scenario in ('timeout','mixed_incident') else 200)
        assert response.headers['traceparent'].split('-')[1]==data['trace_id']
    records=client.get(args.api+'/records',headers={'x-lab-key':'demo-b'}).json()
    checks['tenant_isolation']=all(r['tenant']=='tenant-b' for r in records) and len(records)>0
    checks['metrics']= 'ai_requests_total' in client.get(args.api+'/metrics').text
    checks['stream']= 'simulated_ttft_seconds' in client.post(args.api+'/stream',json={},headers={'x-lab-key':'demo-a'}).text
    if args.stack:
        # Prometheus scrapes asynchronously; wait for this workload to become queryable.
        deadline=time.monotonic()+20
        while True:
            targets=client.get('http://prometheus:9090/api/v1/targets').json()['data']['activeTargets']
            checks['prometheus_scrape']=any(t['health']=='up' and t['labels'].get('job')=='ai-lab' for t in targets)
            result=client.get('http://prometheus:9090/api/v1/query',params={'query':'sum(ai_requests_total)'}).json()['data']['result']
            checks['prometheus_real_requests']=bool(result) and float(result[0]['value'][1])>=10
            if checks['prometheus_scrape'] and checks['prometheus_real_requests'] or time.monotonic()>=deadline:
                break
            time.sleep(.5)
        checks['grafana_database']=client.get('http://grafana:3000/api/health').json()['database']=='ok'
        assert checks['prometheus_scrape'] and checks['prometheus_real_requests'] and checks['grafana_database']
assert checks['api_health'] and checks['tenant_isolation'] and checks['metrics'] and checks['stream']
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks,indent=2))
