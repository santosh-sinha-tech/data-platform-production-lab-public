"""Experiment CLI; measured artifacts and separately persisted predictions."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version, PackageNotFoundError
import json
import os
from pathlib import Path
import platform
import random
import resource
import statistics
import time
from .answers import generate
from .data import read, chunk_documents, validate
from .metrics import evaluate_answer, retrieval_metrics
from .retrieval import Index, MODEL, REVISION

ROOT = Path(__file__).resolve().parents[2]

def mean(values):
    valid = [x for x in values if x is not None]
    return statistics.mean(valid) if valid else None


def percentile(values, p):
    ordered = sorted(values)
    return ordered[max(0,math_ceil(p*len(ordered))-1)]


def math_ceil(x):
    return int(-(-x//1))


def write_csv(path: Path, rows: list[dict]):
    with path.open('w',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def failure_tags(answer, question, score, ranking, documents, ledger):
    tags = []
    retrieved = set(ranking)
    relevant = set(question['relevance'])
    if relevant and not relevant <= retrieved:
        tags.append('Retrieval miss')
    if relevant & retrieved and not relevant & set(answer['evidence']):
        tags.append('Relevant evidence retrieved but not used')
    if score['fact_precision'] is not None and score['fact_precision'] < 1 or score['fact_recall'] is not None and score['fact_recall'] < 1:
        tags.append('Incorrect answer synthesis')
    if score['claim_support'] is not None and score['claim_support'] < 1:
        tags.append('Unsupported claim')
    if score['citation_precision'] is not None and score['citation_precision'] < 1:
        tags.append('Incorrect citation')
    if score['contradictions'] or question['category'] == 'conflict' and len(set(answer['evidence']) & relevant) > 1:
        tags.append('Conflicting evidence')
    stale = {p['id'] for d in documents if not d['current'] for p in d['passages']}
    if stale & (set(answer['evidence']) | {c for claim in answer['claims'] for c in claim['citations']}):
        tags.append('Stale source')
    if score['failure_to_abstain']:
        tags.append('Missing evidence / failure to abstain')
    return tags


def container_limits() -> dict:
    """Expose cgroup constraints separately from host-visible CPU/RAM counts."""
    limits = {}
    for key, path in [('cpu_max','/sys/fs/cgroup/cpu.max'), ('memory_max','/sys/fs/cgroup/memory.max')]:
        try:
            limits[key] = Path(path).read_text().strip()
        except OSError:
            limits[key] = None
    return limits


def run(config: dict, output: Path, lexical_only=False, local_bm25=False) -> dict:
    if config['repetitions'] < 2 or config['warmups'] < 1 or config['top_k'] < 1 or config['evidence_limit'] < 1:
        raise ValueError('Require repeated measurements, warmup, positive K and evidence limit')
    if local_bm25 and not lexical_only:
        raise ValueError('--local-bm25 requires --lexical-only')
    started = datetime.now(timezone.utc).isoformat()
    random.seed(config['seed'])
    documents = read(ROOT/'data/documents.json')
    refs = read(ROOT/'data/references.json')
    adjudications = read(ROOT/'data/adjudications.json')
    fixtures = read(ROOT/'data/answer_fixtures.json')
    validate(documents['documents'], refs, adjudications, fixtures)
    chunks = chunk_documents(documents['documents'],config['chunk_size'],config['overlap'])
    t = time.perf_counter()
    index = Index(chunks,'bm25' if lexical_only else 'all',local_bm25)
    build_ms = (time.perf_counter()-t)*1000
    methods = ['bm25_local' if local_bm25 else 'bm25'] + ([] if lexical_only else ['dense','hybrid'])
    questions = refs['questions'][:config['question_limit']]
    retrieval_rows, answer_rows, predictions, latency_rows, failures = [], [], [], [], []
    ledger = adjudications['claims']
    qmap = {q['id']:q for q in refs['questions']}
    def score_answer(answer, q, method, source, ranking):
        score = evaluate_answer(answer,q,ledger)
        tags = failure_tags(answer,q,score,ranking,documents['documents'],ledger)
        answer_rows.append(dict(id=answer['id'],question_id=q['id'],method=method,source=source,category=q['category'],kind=answer.get('kind','extractive'),**score,failures='; '.join(tags)))
        predictions.append(dict(**answer,method=method,source=source))
        for tag in tags:
            failures.append((answer['id'],q['id'],method,tag))
    for method in methods:
        for q in questions:
            for _ in range(config['warmups']):
                index.search(q['question'],method,config['top_k'],config['rrf_constant'])
            samples, end_to_end = [], []
            for rep in range(config['repetitions']):
                t = time.perf_counter()
                result = index.search(q['question'],method,config['top_k'],config['rrf_constant'])
                retrieval_ms = (time.perf_counter()-t)*1000
                answer = generate(q['question'],result,config['evidence_limit'])
                e2e_ms = (time.perf_counter()-t)*1000
                samples.append(retrieval_ms)
                end_to_end.append(e2e_ms)
                latency_rows.append(dict(method=method,question_id=q['id'],repetition=rep,retrieval_ms=retrieval_ms,pipeline_ms=e2e_ms))
            ranking = [c.passage_id for c in result]
            score = retrieval_metrics(ranking,q['relevance'],config['top_k'])
            retrieval_rows.append(dict(method=method,question_id=q['id'],category=q['category'],difficulty=q['difficulty'],**score,latency_median_ms=statistics.median(samples),latency_p95_ms=percentile(samples,.95),pipeline_median_ms=statistics.median(end_to_end),passages=';'.join(ranking)))
            answer['id'] = f"{method}-{q['id']}"
            score_answer(answer,q,method,'pipeline',ranking)
    for answer in fixtures['answers']:
        score_answer(answer,qmap[answer['question_id']],'fixture','controlled',answer['evidence'])
    summary = {}
    for method in methods:
        subset = [r for r in retrieval_rows if r['method']==method]
        samples = [r['retrieval_ms'] for r in latency_rows if r['method']==method]
        summary[method] = dict(questions=len(subset),scored_questions=sum(r['recall'] is not None for r in subset),**{key:mean([r[key] for r in subset]) for key in ['recall','precision','mrr','ndcg']},latency_median_ms=statistics.median(samples),latency_p95_ms=percentile(samples,.95))
    answer_summary = {}
    keys = ['fact_precision','fact_recall','claim_support','citation_precision','citation_coverage','abstention_correct']
    for method in methods+['fixture']:
        subset = [r for r in answer_rows if r['method']==method]
        answer_summary[method] = dict(n=len(subset),**{key:mean([r[key] for r in subset]) for key in keys},denominators={key:sum(r[key] is not None for r in subset) for key in keys},unadjudicated_claims=sum(r['unadjudicated_claims'] for r in subset))
    categories = {}
    for method in methods:
        categories[method] = {}
        for category in sorted({q['category'] for q in questions}):
            rs=[r for r in retrieval_rows if r['method']==method and r['category']==category]
            ans=[r for r in answer_rows if r['method']==method and r['category']==category]
            categories[method][category]=dict(n=len(rs),retrieval={key:mean([r[key] for r in rs]) for key in ['recall','precision','mrr','ndcg']},answer={key:mean([r[key] for r in ans]) for key in keys})
    libraries = {}
    for name in ['numpy','rank-bm25','sentence-transformers','torch','transformers','huggingface-hub','safetensors','pytest']:
        try: libraries[name]=version(name)
        except PackageNotFoundError: libraries[name]='not installed'
    hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((ROOT/'data').glob('*.json'))}
    physical_memory = os.sysconf('SC_PHYS_PAGES')*os.sysconf('SC_PAGE_SIZE') if hasattr(os,'sysconf') and 'SC_PHYS_PAGES' in os.sysconf_names else None
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    metrics=dict(dataset_version=documents['version'],dataset_sha256=hashes,seed=config['seed'],configuration=config,started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat(),libraries=libraries,
        machine=dict(os=platform.system(),release=platform.release(),architecture=platform.machine(),python=platform.python_version(),logical_cpus=os.cpu_count(),physical_memory_bytes=physical_memory,cgroup_v2=container_limits(),peak_rss_bytes=rss if platform.system()=='Darwin' else rss*1024),
        model=None if lexical_only else dict(id=MODEL,revision=REVISION,device='cpu',dimensions=384),mode='lexical-only' if lexical_only else 'all',skipped_methods=['dense','hybrid'] if lexical_only else [],
        index=dict(documents=len(documents['documents']),passages=sum(len(d['passages']) for d in documents['documents']),chunks=len(chunks),build_ms=build_ms,vector_bytes=0 if lexical_only else int(index.vectors.nbytes)),retrieval=summary,answers=answer_summary,per_category=categories,
        latency_protocol='Sequential warmed serial queries; retrieval includes tokenization/query embedding/fusion, excludes index build; pipeline adds evidence selection and extractive generation, excludes evaluation and report I/O. P95 nearest rank; each query repeated; method order fixed (thermal/order confounder).',
        correctness_protocol='Closed-world manually adjudicated exact claim identity; unknown claims conservatively receive zero support/correctness and are counted. Not a general factuality verifier. Null metrics excluded from macro means; empty claims have undefined precision/support; unanswerable cases have undefined retrieval metrics unless conflict qrels exist.')
    output.mkdir(parents=True,exist_ok=True)
    (output/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    (output/'predictions.json').write_text(json.dumps(predictions,indent=2)+'\n')
    write_csv(output/'retrieval_comparison.csv',retrieval_rows)
    write_csv(output/'answer_evaluation.csv',answer_rows)
    write_csv(output/'latency_samples.csv',latency_rows)
    actions={
        'Retrieval miss':'Inspect passage qrels; tune K/chunks and test dense/hybrid retrieval.',
        'Relevant evidence retrieved but not used':'Audit evidence budget and selection; rerank with authority constraints.',
        'Incorrect answer synthesis':'Check reference-fact completeness and contradiction handling; expand independently reviewed claim coverage.',
        'Unsupported claim':'Require claim/evidence entailment review; abstain on unsupported additions.',
        'Incorrect citation':'Verify each cited passage is retrieved and supports its attached claim.',
        'Conflicting evidence':'Surface conflicting active sources; route to owner; abstain until resolved.',
        'Stale source':'Apply effective-date/status filters before retrieval, retain stale sources for adversarial tests.',
        'Missing evidence / failure to abstain':'Add calibrated answerability checks and clarification for ambiguous questions.'}
    lines=['# Failure analysis','', 'Synthetic closed-world diagnostic tags; multiple tags may apply. A synthesis tag also includes incomplete reference-fact recall. Retrieval misses can be partial. Conflicts use authored relationships/category labels, not automatic semantic inference.','']
    for tag, action in actions.items():
        examples=[x for x in failures if x[3]==tag]
        lines += [f'## {tag}', '',f'Observed: {len(examples)} tagged rows. Engineering action: {action}', '', 'Examples: '+(', '.join(f'{a} ({q}, {m})' for a,q,m,_ in examples[:5]) or 'none in this run'), '']
    (output/'failure_analysis.md').write_text('\n'.join(lines))
    lines=['# Enterprise RAG benchmark','',f'Dataset {documents["version"]}; {len(questions)} pipeline questions; 10 independently authored controlled answers. All data synthetic. Small samples are diagnostic, not production estimates.','',f'Mode: {metrics["mode"]}. Skipped methods: {", ".join(metrics["skipped_methods"]) or "none"}.','', '| Method | N scored | Recall@K | Precision@K | MRR | nDCG@K | Median ms | P95 ms |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for method,s in summary.items():
        lines.append(f'| {method} | {s["scored_questions"]} | '+ ' | '.join(f'{s[k]:.4f}' for k in ['recall','precision','mrr','ndcg','latency_median_ms','latency_p95_ms'])+' |')
    lines += ['', '## Answer evaluation', '', '| Source | N | Fact precision | Fact recall | Claim support | Citation precision | Citation coverage | Abstention accuracy |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for method,s in answer_summary.items():
        lines.append(f'| {method} | {s["n"]} | '+' | '.join('NA' if s[k] is None else f'{s[k]:.4f}' for k in keys)+' |')
    lines += ['', '## Category detail', '', 'Complete category metrics and per-metric denominators are in metrics.json; per-question and fixture rows are in the CSVs.']
    for method,cats in categories.items():
        for cat,s in cats.items():
            lines.append(f'- {method} / {cat}: n={s["n"]}; recall={s["retrieval"]["recall"]}; fact recall={s["answer"]["fact_recall"]}; abstention accuracy={s["answer"]["abstention_correct"]}.')
    lines += ['', '## Interpretation and limits', '', metrics['correctness_protocol'],'',metrics['latency_protocol'],'',f'Index build: {build_ms:.3f} ms. Peak process RSS: {metrics["machine"]["peak_rss_bytes"]} bytes (whole process high-water mark, not per-method incremental memory). No API charges; CPU/energy opportunity cost is not zero and is not priced here.', '', 'The baseline copies up to two current retrieved chunks. It can cite irrelevant material perfectly, miss required facts, ignore active contradictions, and fail to abstain. Controlled fixtures test scoring independently from retrieval. Same-corpus development results are not held-out generalization evidence. No local generative LLM is required or measured.', '', 'For alternative chunk sizes, qrels remain atomic passage-level labels. Siblings are collapsed before K; any returned fragment counts as retrieving that passage (optimistic for fragmented evidence). Claim scoring remains exact authored text: split claims become unadjudicated, so chunk-sweep answer scores are not directly comparable without new human labels.', '', 'Hardware, versions, dataset hashes, configuration and UTC run times are recorded in metrics.json. Raw warmed latency samples are retained. See failure_analysis.md for observed failure classes.']
    (output/'benchmark_report.md').write_text('\n'.join(lines)+'\n')
    return metrics


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['quick','full'],default='quick')
    parser.add_argument('--config',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'results')
    parser.add_argument('--lexical-only',action='store_true',help='Explicitly skip dense and hybrid')
    parser.add_argument('--local-bm25',action='store_true',help='Explicit dependency-free BM25 variant; labeled bm25_local')
    args=parser.parse_args()
    config=read(args.config or ROOT/f'config/{args.mode}.json')
    result=run(config,args.output,args.lexical_only,args.local_bm25)
    print(json.dumps(dict(mode=result['mode'],retrieval=result['retrieval'],answers=result['answers']),indent=2))

if __name__=='__main__':
    main()
