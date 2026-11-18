"""Validate arithmetic and cross-file correlations in already executed results."""
import csv
import json
import math
from pathlib import Path

root=Path(__file__).resolve().parents[1]
for path in (root/'results',root/'results/quick'):
    metrics=json.loads((path/'metrics.json').read_text())
    aggregate=metrics['aggregate']
    rows=list(csv.DictReader((path/'scenario_comparison.csv').open()))
    assert sum(int(r['requests']) for r in rows)==aggregate['requests']
    assert sum(int(r['transport_success']) for r in rows)==aggregate['transport_success']
    assert math.isclose(sum(float(r['cost']) for r in rows),aggregate['cost'])
    costs=list(csv.DictReader((path/'cost_analysis.csv').open()))
    for dimension in ('tenant','application','model','request'):
        assert math.isclose(sum(float(c['cost']) for c in costs if c['dimension']==dimension),aggregate['cost'])
    for run in range(metrics['runs']):
        spans=json.loads((path/f'traces-run-{run}.json').read_text())
        ids={s['span_id'] for s in spans}
        assert all(s['parent_id'] in ids for s in spans if s['name']!='inbound_request')
        assert len([s for s in spans if s['name']=='inbound_request'])==10
        assert {s['trace_id'] for s in spans}=={t['trace_id'] for t in metrics['trace_examples'] if t['run']==run}
    required=('benchmark_report.md','metrics.json','scenario_comparison.csv','slo_report.md',
              'failure_analysis.md','cost_analysis.csv','dashboard.html')
    assert all((path/name).is_file() for name in required)
    print(f'{path.name}: PASS; {aggregate["requests"]} requests, costs reconcile across dimensions; trace parents/correlations verified')
