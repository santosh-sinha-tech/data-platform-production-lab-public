"""Independent CSV-to-JSON reconciliation (does not call metric implementations)."""
import csv
import json
from pathlib import Path
import statistics
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else 'results')
metrics=json.loads((root/'metrics.json').read_text())
def rows(name):
    with (root/name).open() as stream: return list(csv.DictReader(stream))
retrieval=rows('retrieval_comparison.csv')
answers=rows('answer_evaluation.csv')
latency=rows('latency_samples.csv')
for method, summary in metrics['retrieval'].items():
    subset=[r for r in retrieval if r['method']==method]
    assert len(subset)==summary['questions']
    for key in ['recall','precision','mrr','ndcg']:
        values=[float(r[key]) for r in subset if r[key]!='']
        assert abs(statistics.mean(values)-summary[key])<1e-12
    samples=[float(r['retrieval_ms']) for r in latency if r['method']==method]
    assert len(samples)==len(subset)*metrics['configuration']['repetitions']
    assert abs(statistics.median(samples)-summary['latency_median_ms'])<1e-12
    ordered=sorted(samples)
    import math
    assert abs(ordered[math.ceil(.95*len(ordered))-1]-summary['latency_p95_ms'])<1e-12
for method, summary in metrics['answers'].items():
    subset=[r for r in answers if r['method']==method]
    assert len(subset)==summary['n']
    for key,n in summary['denominators'].items():
        values=[float(r[key]) for r in subset if r[key]!='']
        assert len(values)==n
        if values: assert abs(statistics.mean(values)-summary[key])<1e-12
for method,categories in metrics['per_category'].items():
    for category,summary in categories.items():
        subset=[r for r in retrieval if r['method']==method and r['category']==category]
        assert len(subset)==summary['n']
        for key,value in summary['retrieval'].items():
            values=[float(r[key]) for r in subset if r[key]!='']
            assert (not values and value is None) or abs(statistics.mean(values)-value)<1e-12
        answer_subset=[r for r in answers if r['method']==method and r['category']==category]
        for key,value in summary['answer'].items():
            values=[float(r[key]) for r in answer_subset if r[key]!='']
            assert (not values and value is None) or abs(statistics.mean(values)-value)<1e-12
print('PASS: aggregate/category retrieval, answer denominators, latency samples, medians and P95 reconcile')
