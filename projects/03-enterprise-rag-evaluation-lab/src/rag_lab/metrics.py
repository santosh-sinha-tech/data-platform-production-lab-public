"""Hand-checkable retrieval metrics and authoritative closed-world claim scoring."""
import math


def retrieval_metrics(ranking: list[str], grades: dict[str,int], k: int) -> dict:
    if len(ranking) != len(set(ranking)) or k < 1:
        raise ValueError('Unique passage IDs and positive K required')
    ranking = ranking[:k]
    relevant = {p for p,g in grades.items() if g > 0}
    if not relevant:
        return dict(recall=None,precision=None,mrr=None,ndcg=None)
    hits = [int(p in relevant) for p in ranking]
    dcg = sum((2**grades.get(p,0)-1)/math.log2(i+2) for i,p in enumerate(ranking))
    ideal = sum((2**g-1)/math.log2(i+2) for i,g in enumerate(sorted(grades.values(),reverse=True)[:k]))
    return dict(recall=sum(hits)/len(relevant),precision=sum(hits)/k,mrr=next((1/(i+1) for i,h in enumerate(hits) if h),0),ndcg=dcg/ideal)


def evaluate_answer(answer: dict, question: dict, ledger: dict) -> dict:
    # This exact-text identity lookup is a closed-world adjudication lookup, NOT a factuality heuristic.
    lookup = {v['text']:v for v in ledger.values()}
    expected = [ledger[f]['text'] for f in question['expected_facts']]
    texts = [c['text'] for c in answer['claims']]
    correct = sum(t in expected for t in texts)
    supported = cited_supported = citation_hits = total_citations = contradictions = unknown = 0
    evidence = set(answer['evidence'])
    for claim in answer['claims']:
        label = lookup.get(claim['text'])
        if label is None:
            unknown += 1
            label = {'supports':[], 'contradicts':[]}
        supports = set(label['supports'])
        supported += bool(supports & evidence)
        contradictions += bool(set(label['contradicts']) & evidence)
        valid = [c in supports and c in evidence for c in claim['citations']]
        cited_supported += any(valid)
        citation_hits += sum(valid)
        total_citations += len(valid)
    n = len(texts)
    precision = correct/n if n else None
    recall = len(set(expected)&set(texts))/len(set(expected)) if expected else None
    return dict(fact_precision=precision,fact_recall=recall,claim_support=supported/n if n else None,
        citation_precision=citation_hits/total_citations if total_citations else None,
        citation_coverage=cited_supported/n if n else None,contradictions=contradictions,unadjudicated_claims=unknown,
        abstention_correct=int(answer['abstain'] == (not question['answerable'])),
        appropriate_abstention=int(answer['abstain'] and not question['answerable']),
        failure_to_abstain=int(not answer['abstain'] and not question['answerable']))
