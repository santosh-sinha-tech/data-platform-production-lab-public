"""Independent-process repetitions and descriptive variability; never pool run samples."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from .model import summarize


def normalize_plan(text: str) -> str:
    """Remove only generated expression/stage IDs and physical input location URIs."""
    text = re.sub(r'#\d+L?', '#ID', text)
    text = re.sub(r'plan_id=\d+', 'plan_id=ID', text)
    return re.sub(r'file:[^\]\s,]+', 'file:<INPUT>', text)


def variability(values: list[float]) -> dict:
    if len(values) < 3:
        raise ValueError('at least three independent runs required for spread statistics')
    stats = summarize(values)
    mean = statistics.mean(values)
    sd = statistics.stdev(values)
    return dict(stats, mean=mean, sample_stdev=sd, cv_percent=100*sd/mean)


def scan_metadata(path: Path, rounds: int) -> dict:
    """Untruncated executed scan metadata, checked across every timed/warmup execution."""
    found = {q:{l:[] for l in ('fragmented','compacted')}
             for q in ('full_aggregation','selective','partition_pruned')}
    def walk(node: dict) -> None:
        metadata = node.get('metadata',{})
        schema = metadata.get('ReadSchema','')
        location = metadata.get('Location','')
        layout = next((l for l in ('fragmented','compacted') if f'/data/{l}' in location),None)
        if layout and schema in ('struct<region:string,amount_cents:bigint>',
                                 'struct<customer_id:bigint,region:string,amount_cents:bigint,status:string>'):
            query = ('selective' if 'customer_id' in schema else
                     'partition_pruned' if metadata.get('PartitionFilters','[]')!='[]' else 'full_aggregation')
            found[query][layout].append({k:normalize_plan(v) for k,v in metadata.items()})
        for child in node.get('children',[]):
            walk(child)
    for file in (path/'events').rglob('*'):
        if not file.is_file() or file.name.startswith('.'):
            continue
        for line in file.open():
            event=json.loads(line)
            if event.get('Event','').endswith('SparkListenerSQLExecutionStart'):
                walk(event['sparkPlanInfo'])
    result={}
    for q,layouts in found.items():
        if not any(layouts.values()):
            continue
        result[q]={}
        for layout,values in layouts.items():
            if len(values)!=rounds or any(v!=values[0] for v in values):
                raise ValueError(f'missing or inconsistent executed scan metadata: {q}/{layout}')
            result[q][layout]={'executions_checked':len(values),'metadata':values[0]}
        if result[q]['fragmented']['metadata']!=result[q]['compacted']['metadata']:
            raise ValueError(f'executed scan metadata differs: {q}')
    (path/'plans'/'scan-metadata.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def complete_plan(text: str, metadata: dict) -> str:
    """Restore the display-truncated DataFilters from checked event-log metadata."""
    return normalize_plan(re.sub(r'DataFilters: \[.*?(?=, Format:)',
        lambda match: 'DataFilters: '+metadata['DataFilters'],text))


def analyze(paths: list[Path], destination: Path) -> dict:
    reports = [json.loads((p/'report.json').read_text()) for p in paths]
    if len(reports) < 2 or len({r['run_id'] for r in reports}) != len(reports):
        raise ValueError('need distinct independent runs')
    baseline = reports[0]
    audits = []
    for path,r in zip(paths,reports):
        settings = {k:v for k,v in r['environment']['spark_settings'].items() if k!='spark.eventLog.dir'}
        base_settings = {k:v for k,v in baseline['environment']['spark_settings'].items() if k!='spark.eventLog.dir'}
        if r['config'] != baseline['config'] or settings != base_settings or r['output_checksums'] != baseline['output_checksums']:
            raise ValueError('config, settings or outputs differ across runs')
        if any(r['environment'][k]!=baseline['environment'][k] for k in ('spark_version','python','java','local_cores','cgroup_cpu_max','cgroup_memory_max')):
            raise ValueError('runtime/resources differ across runs')
        f,c = [r['layouts'][l] for l in ('fragmented','compacted')]
        for key in ('fingerprint','schema','bucket_rows','partition_directories'):
            if f[key] != c[key] or f[key] != baseline['layouts']['fragmented'][key]:
                raise ValueError(f'fairness check failed: {key}')
        executed_metadata = scan_metadata(path,r['config']['warmups']+r['config']['iterations'])
        if set(executed_metadata)!=set(r['queries']):
            raise ValueError('missing executed query scan metadata')
        plan_checks = {}
        for q in r['queries']:
            fp,cp = [complete_plan((path/'plans'/f'{q}-{l}.txt').read_text(),executed_metadata[q][l]['metadata']) for l in ('fragmented','compacted')]
            same = fp == cp
            if not same:
                raise ValueError(f'normalized plan differs: {r["run_id"]} {q}')
            plan_checks[q] = {'equal_after_normalization':same,'sha256':hashlib.sha256(fp.encode()).hexdigest()}
        audits.append({'run_id':r['run_id'],'plans':plan_checks,
            'file_counts':{l:r['layouts'][l]['files'] for l in ('fragmented','compacted')},
            'parquet_bytes':{l:r['layouts'][l]['parquet_bytes'] for l in ('fragmented','compacted')},
            'byte_ratio':r['fragmented_to_compacted_byte_ratio'],
            'scan_partition_count_proxy':r['scan_partition_count_proxy'],
            'compaction_seconds':r['measured_compaction_seconds']})
    summary = {}
    csv_rows = []
    for q in baseline['queries']:
        f = [r['queries'][q]['fragmented']['median_seconds'] for r in reports]
        c = [r['queries'][q]['compacted']['median_seconds'] for r in reports]
        savings = [a-b for a,b in zip(f,c)]
        ratios = [a/b for a,b in zip(f,c)]
        summary[q] = {'fragmented_run_medians':variability(f),'compacted_run_medians':variability(c),
            'paired_savings_seconds':savings,'median_paired_savings_seconds':statistics.median(savings),
            'min_paired_savings_seconds':min(savings),'max_paired_savings_seconds':max(savings),
            'paired_savings_sample_stdev':statistics.stdev(savings),
            'ratios':ratios,'median_ratio':statistics.median(ratios),
            'runs_favoring_compaction':sum(s>0 for s in savings)}
        for r in reports:
            a,b = [r['queries'][q][l] for l in ('fragmented','compacted')]
            csv_rows.append(dict(run_id=r['run_id'],query=q,fragmented_median=a['median_seconds'],
                compacted_median=b['median_seconds'],fragmented_iqr=a['iqr_seconds'],compacted_iqr=b['iqr_seconds'],
                saved_seconds=a['median_seconds']-b['median_seconds'],ratio=a['median_seconds']/b['median_seconds']))
    result = {'independent_runs':len(paths),'config':baseline['config'],'queries':summary,'fairness_audits':audits,
              'aggregation':'descriptive statistics across per-run medians; samples not pooled',
              'plan_normalization':'expression IDs, plan IDs and file URIs; display-truncated DataFilters restored from full, equality-checked executed scan metadata; original plans retained',
              'limitations':'Fresh JVM per run; sequential runs on one host. OS caches not evicted. Fixed query order; alternating layout order. No statistical significance or causal file-count-only claim.'}
    destination.mkdir(parents=True,exist_ok=True)
    (destination/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    with (destination/'run-medians.csv').open('w',newline='') as handle:
        w=csv.DictWriter(handle,fieldnames=list(csv_rows[0]),lineterminator='\n');w.writeheader();w.writerows(csv_rows)
    lines=['# Independent-run repeatability validation','',f'{len(paths)} fresh Python/JVM applications. Each run generates and validates its own layouts before timing. No concurrent benchmark processes.','',
        '| Query | Fragmented median of run medians s [min–max]; CV | Compacted median of run medians s [min–max]; CV | Paired saving median s [min–max] | Runs favoring compaction |',
        '|---|---|---|---|---|']
    for q,x in summary.items():
        a,b=[x[f'{l}_run_medians'] for l in ('fragmented','compacted')]
        lines.append(f"| {q} | {a['median_seconds']:.6f} [{a['min_seconds']:.6f}–{a['max_seconds']:.6f}]; {a['cv_percent']:.1f}% | {b['median_seconds']:.6f} [{b['min_seconds']:.6f}–{b['max_seconds']:.6f}]; {b['cv_percent']:.1f}% | {x['median_paired_savings_seconds']:.6f} [{x['min_paired_savings_seconds']:.6f}–{x['max_paired_savings_seconds']:.6f}] | {x['runs_favoring_compaction']}/{len(paths)} |")
    lines+=['','CV is sample standard deviation / mean across independent run medians. Within-run IQRs and all paired results are in run-medians.csv; individual reports preserve every raw sample. Negative savings mean compaction was slower. These are descriptive statistics, not confidence intervals.','',
        '## Fairness checks','',
        'All runs pass identical row counts, cents totals, two independent row-hash sums, schema, bucket row counts, bucket directory names, query-output checksums, relevant Spark settings and runtime/resource configuration. Hash sums remain probabilistic. Explain plans match across layouts after removing expression IDs, plan IDs and input file URIs and restoring display-truncated DataFilters from complete Spark event metadata. All executed scan metadata are compared across layouts/iterations; scan-metadata.json preserves these fields. The normalized plan check preserves operators, columns, filters, exchanges, read schemas and partition strategy; it does not claim equal physical work. Actual scan partition proxies and bytes/files are retained in summary.json.','',
        '## Interpretation and cost boundary','',
        'Layout is the intervention: file count, file sizes, row ordering, compression/encoding, footer overhead, scan packing and row-group pruning can change together. Do not attribute all elapsed-time differences solely to file count. This is a warm-storage local experiment; fresh JVMs do not clear OS caches. Host activity, JIT and fixed query order remain limitations. No significance claim or cloud extrapolation.','',
        'Break-even amortizes the processing time of one measured rewrite against assumed stable future per-query savings. It excludes cloud infrastructure pricing/billing, object-store requests, idle/shared capacity and recurring compaction cycles. A supplied hourly rate is only a compute-time conversion. Repeated maintenance must be evaluated over a horizon including every rewrite and actual workload/billing data.','']
    (destination/'summary.md').write_text('\n'.join(lines))
    return result


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=Path('config/quick.json'))
    parser.add_argument('--repeats',type=int,default=5)
    parser.add_argument('--output',type=Path,default=Path('runs/repeatability'))
    args=parser.parse_args()
    if args.repeats < 3:
        parser.error('at least 3 repetitions required for spread statistics; use >=5 for publication checks')
    destination=args.output.resolve()/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    destination.mkdir(parents=True,exist_ok=False)
    paths=[]
    for i in range(args.repeats):
        root=destination/f'repetition-{i+1}'
        with (destination/f'repetition-{i+1}.log').open('w') as log:
            subprocess.run([sys.executable,'-m','small_files.cli','--config',str(args.config),'--output',str(root)],stdout=log,stderr=subprocess.STDOUT,check=True)
        reports=list(root.glob('*/report.json'))
        if len(reports)!=1:
            raise ValueError('missing or ambiguous successful report')
        paths.append(reports[0].parent)
        print(f'Completed repetition {i+1}/{args.repeats}',flush=True)
    analyze(paths,destination)
    print(f'REPEATABILITY_DIR={destination}',flush=True)

if __name__=='__main__':
    main()
