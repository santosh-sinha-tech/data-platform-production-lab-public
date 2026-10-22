"""Run one isolated experiment; only a complete run emits report.json."""
import argparse
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import time
import uuid

from pyspark.sql import SparkSession, DataFrame, functions as F
from .data import generate, fingerprint, read, write_layout
from .model import Config, file_stats, summarize, break_even

SETTINGS = {
    'spark.sql.session.timeZone': 'UTC',
    'spark.sql.adaptive.enabled': 'false',
    'spark.sql.shuffle.partitions': '4',
    'spark.sql.parquet.compression.codec': 'snappy',
    'spark.sql.files.maxPartitionBytes': '134217728',
    'spark.sql.files.openCostInBytes': '4194304',
    'spark.sql.parquet.filterPushdown': 'true',
    'spark.sql.parquet.enableVectorizedReader': 'true',
    'spark.sql.parquet.aggregatePushdown': 'false',
    'spark.eventLog.enabled': 'true',
    'spark.eventLog.compress': 'false',
    'spark.ui.enabled': 'false',
    'spark.driver.memory': '1g',
}

def query(df: DataFrame, name: str) -> DataFrame:
    if name == 'selective':
        df = df.filter((F.col('customer_id') < 1000) & (F.col('status') == 'confirmed'))
    elif name == 'partition_pruned':
        df = df.filter(F.col('event_bucket') == 0)
    return df.groupBy('region').agg(F.count('*').alias('records'), F.sum('amount_cents').alias('amount_cents'))

def output_digest(rows: list) -> str:
    canonical = sorted([r.asDict() for r in rows], key=lambda r: r['region'])
    return hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()

def event_metrics(directory: Path) -> dict:
    """Measured successful task attempts across entire application, NOT per query."""
    result = {'scope': 'whole application including generation, validation, warmups, measured reads',
              'successful_task_attempts': 0, 'input_bytes': 0, 'input_records': 0,
              'shuffle_read_bytes': 0, 'shuffle_write_bytes': 0}
    for path in directory.rglob('*'):
        if not path.is_file() or path.name.startswith('.'):
            continue
        for line in path.read_text().splitlines():
            event = json.loads(line)
            if event.get('Event') != 'SparkListenerTaskEnd' or event.get('Task End Reason',{}).get('Reason') != 'Success':
                continue
            m = event.get('Task Metrics', {})
            result['successful_task_attempts'] += 1
            result['input_bytes'] += m.get('Input Metrics',{}).get('Bytes Read',0)
            result['input_records'] += m.get('Input Metrics',{}).get('Records Read',0)
            sr = m.get('Shuffle Read Metrics',{})
            result['shuffle_read_bytes'] += sr.get('Remote Bytes Read',0)+sr.get('Local Bytes Read',0)
            result['shuffle_write_bytes'] += m.get('Shuffle Write Metrics',{}).get('Shuffle Bytes Written',0)
    return result

def render(result: dict) -> str:
    lines = ['# Small Files Performance Lab — measured run', '',
        f"Run: `{result['run_id']}`; started UTC: {result['started_utc']}", '',
        'Synthetic data. Warm filesystem/JVM experiment; no guaranteed performance improvement.', '',
        '## Environment', '', '```json', json.dumps(result['environment'],indent=2), '```', '',
        '## Layouts and validation', '', '```json', json.dumps(result['layouts'],indent=2,default=str), '```', '',
        f"Fragmented/compacted Parquet byte ratio: {result['fragmented_to_compacted_byte_ratio']:.3f}. Comparability warning (>25% difference): {result['byte_comparability_warning']}.", '',
        'Order-independent fingerprints match the generated source. Hash aggregates are probabilistic checks, not proof of multiset equality.', '',
        '## Query results', '',
        '| Query | Fragmented median s | Compacted median s | F/C ratio | Fragmented IQR s | Compacted IQR s |',
        '|---|---:|---:|---:|---:|---:|']
    for name, comparison in result['queries'].items():
        f,c = comparison['fragmented'],comparison['compacted']
        lines.append(f"| {name} | {f['median_seconds']:.6f} | {c['median_seconds']:.6f} | {f['median_seconds']/c['median_seconds']:.3f} | {f['iqr_seconds']:.6f} | {c['iqr_seconds']:.6f} |")
    lines += ['', 'Ratio >1 favors compaction; <1 favors fragmentation. See JSON/CSV for every sample and output checksum.', '',
        '## Economics', '', f"Measured rewrite duration: {result['measured_compaction_seconds']:.6f} s. Includes fragmented read, redistribution and write; excludes validation.", '',
        'Each query is modeled as a separate future workload; do not add these break-even counts.', '',
        '```json', json.dumps(result['economics'],indent=2), '```', '',
        'A zero hourly rate means no monetary conclusion. Time break-even still applies. Sensitivity varies observed savings by 0.5/1/1.5 and rate by 0/1/2 of supplied rate; these are scenarios, not confidence intervals.', '',
        '## Measurement boundaries', '',
        'Wall time includes relation creation, file listing, planning, execution and collection of small aggregates. No Spark cache/persist is used. Validation and warmups warm OS caches. Layout order alternates each round; query order is fixed. Single application, no cache eviction or cold-storage claim. JVM JIT, host contention, compression differences, tiny-data overhead and Docker virtualization remain confounders.', '',
        'Parquet file bytes are filesystem lengths, not runtime scan bytes. Scan RDD partition counts in JSON are planning proxies, not measured tasks. Explain plans are post-action plans. Event metrics below are application-wide measured task counters and include validation/writes; they cannot attribute query savings.', '',
        '```json', json.dumps(result['application_metrics'],indent=2), '```', '',
        '## Configuration', '', '```json', json.dumps(result['config'],indent=2), '```', '',
        'Local results do not predict cloud object-store request latency, throttling, egress, cluster startup or actual billing. Repeat larger runs on the deployment storage before choosing compaction policy.', '']
    return '\n'.join(lines)

def run(config: Config, root: Path) -> Path:
    config.validate()
    started = datetime.now(timezone.utc).isoformat()
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    out = root.resolve()/run_id
    out.mkdir(parents=True, exist_ok=False)
    (out/'events').mkdir()
    (out/'plans').mkdir()
    (out/'config.json').write_text(json.dumps(asdict(config),indent=2))
    spark = None
    try:
        builder = SparkSession.builder.master(f'local[{config.cores}]').appName('small-files-lab')
        settings = dict(SETTINGS, **{'spark.eventLog.dir': (out/'events').as_uri()})
        for key,value in settings.items():
            builder = builder.config(key,value)
        spark = builder.getOrCreate()
        spark.sparkContext.setLogLevel('WARN')
        if not spark.version.startswith('3.5.'):
            raise ValueError('requires Spark 3.5.x')
        source = generate(spark, config.rows, config.seed, config.partitions)
        expected = fingerprint(source)
        paths = {name: out/'data'/name for name in ('fragmented','compacted')}
        write_layout(source,paths['fragmented'],config.fragmented_files,config.partitions,config.partitioned)
        t = time.perf_counter()
        write_layout(read(spark, paths['fragmented']),paths['compacted'],config.compacted_files,config.partitions,config.partitioned)
        compaction = time.perf_counter()-t
        layouts = {}
        for name,path in paths.items():
            actual = fingerprint(read(spark,path))
            if actual != expected or actual['rows'] != config.rows:
                raise ValueError(f'logical equivalence failed: {name}')
            layouts[name] = dict(file_stats(path), fingerprint=actual)
        if layouts['fragmented']['files'] <= layouts['compacted']['files']:
            raise ValueError('layouts are not physically distinct')
        ratio = layouts['fragmented']['parquet_bytes']/layouts['compacted']['parquet_bytes']
        names = ['full_aggregation','selective'] + (['partition_pruned'] if config.partitioned else [])
        samples = {q:{l:[] for l in paths} for q in names}
        checksums = {}
        records = []
        proxies = {}
        for q in names:
            for iteration in range(config.warmups+config.iterations):
                order = list(paths) if iteration % 2 == 0 else list(reversed(paths))
                for position,name in enumerate(order):
                    spark.catalog.clearCache()
                    begin = time.perf_counter()
                    frame = read(spark,paths[name])
                    plan = query(frame,q)
                    rows = plan.collect()
                    elapsed = time.perf_counter()-begin
                    digest = output_digest(rows)
                    if q in checksums and checksums[q] != digest:
                        raise ValueError(f'query checksum mismatch: {q}')
                    checksums[q] = digest
                    measured = iteration >= config.warmups
                    records.append(dict(query=q,layout=name,iteration=iteration,position=position,
                                        measured=measured,seconds=elapsed,checksum=digest,
                                        matched_records=sum(r['records'] for r in rows)))
                    if measured:
                        samples[q][name].append(elapsed)
                    if iteration == config.warmups:
                        (out/'plans'/f'{q}-{name}.txt').write_text(plan._jdf.queryExecution().toString())
                        # A proxy obtained outside timed work; not executed-task telemetry.
                        proxies[f'{q}/{name}'] = (frame.filter('event_bucket=0') if q=='partition_pruned' else frame).rdd.getNumPartitions()
        queries = {q:{l:summarize(samples[q][l]) for l in paths} for q in names}
        economics = {}
        cost_seconds = compaction if config.compaction_seconds is None else config.compaction_seconds
        for q in names:
            f,c = [queries[q][l]['median_seconds'] for l in paths]
            economics[q] = {'base':break_even(cost_seconds,f,c,config.compute_hour_cost),
                'compaction_time_source':'measured' if config.compaction_seconds is None else 'user_supplied',
                'sensitivity':[dict(savings_multiplier=s,rate_multiplier=r,
                    **break_even(cost_seconds,max(f-c,0)*s,0,config.compute_hour_cost*r))
                    for s in (0.5,1,1.5) for r in (0,1,2)] if f>c else []}
        environment = {'spark_version':spark.version,'python':sys.version,'java':spark._jvm.java.lang.System.getProperty('java.version'),
            'platform':platform.platform(),'machine':platform.machine(),'visible_cpu_count':os.cpu_count(),
            'local_cores':config.cores,'physical_memory_bytes':os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES'),
            'disk_free_before_cleanup_bytes':shutil.disk_usage(out).free,
            'spark_settings':{k:spark.conf.get(k) for k in settings},
            'cgroup_memory_max':Path('/sys/fs/cgroup/memory.max').read_text().strip() if Path('/sys/fs/cgroup/memory.max').exists() else None,
            'cgroup_cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip() if Path('/sys/fs/cgroup/cpu.max').exists() else None}
        spark.stop()
        spark = None
        result = dict(run_id=run_id,started_utc=started,config=asdict(config),environment=environment,
            layouts=layouts,fragmented_to_compacted_byte_ratio=ratio,
            byte_comparability_warning=abs(ratio-1)>0.25,queries=queries,
            output_checksums=checksums,scan_partition_count_proxy=proxies,
            measured_compaction_seconds=compaction,economics=economics,
            application_metrics=event_metrics(out/'events'))
        with (out/'samples.csv').open('w',newline='') as handle:
            writer = csv.DictWriter(handle,fieldnames=list(records[0]),lineterminator="\n")
            writer.writeheader()
            writer.writerows(records)
        (out/'report.md').write_text(render(result))
        (out/'report.json').write_text(json.dumps(result,indent=2,default=str,allow_nan=False)+'\n')
        return out
    except Exception as exc:
        (out/'FAILED.json').write_text(json.dumps({'error_type':type(exc).__name__,'message':str(exc)}))
        raise
    finally:
        if spark is not None:
            spark.stop()

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=Path('config/quick.json'))
    parser.add_argument('--output',type=Path,default=Path('runs'))
    args = parser.parse_args()
    try:
        config = Config(**json.loads(args.config.read_text()))
        print(f'RESULT_DIR={run(config,args.output)}')
    except (ValueError,TypeError,OSError) as exc:
        parser.exit(1,f'Lab failed: {exc}\n')

if __name__ == '__main__':
    main()
