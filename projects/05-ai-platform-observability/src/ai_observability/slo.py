import math
from typing import Sequence

def percentile(values: Sequence[float], q: float) -> float:
    """Nearest rank: sorted x[ceil(q*n)-1], q in (0,1]."""
    if not 0 < q <= 1:
        raise ValueError('q must be in (0,1]')
    if not values:
        return 0.0
    return sorted(values)[math.ceil(q * len(values)) - 1]

def budget(good: int, total: int, target: float) -> dict:
    if not 0 <= good <= total or not 0 < target < 1:
        raise ValueError('invalid population or target')
    allowed = total * (1-target)
    bad = total-good
    return dict(good=good,total=total,target=target,sli=good/total if total else None,
                allowed_bad=allowed,bad=bad,remaining=allowed-bad,
                consumption=bad/allowed if allowed else None)

def objectives(rows: list[dict]) -> dict:
    eligible = [r for r in rows if r['status'] != 429]
    success = [r for r in eligible if r['status']==200]
    return {'availability':budget(len(success),len(eligible),.99),
            'latency':budget(sum(r.get('client_latency',r['latency'])<=.08 for r in eligible),len(eligible),.95),
            'quality':budget(sum(r['quality']['passed'] for r in success),len(success),.95),
            'cost':budget(sum(r['cost']<=.001 for r in eligible),len(eligible),.99)}

def burn(events: list[dict], end: int, window: int, target: float=.99) -> float:
    selected=[e for e in events if end-window < e['minute'] <= end]
    return sum(e['bad'] for e in selected)/len(selected)/(1-target) if selected else 0.0

def alerts(events: list[dict], end: int) -> dict:
    rates={str(w):burn(events,end,w) for w in (5,30,60,360)}
    return dict(rates=rates,page=rates['5']>=14.4 and rates['60']>=14.4,
                ticket=rates['30']>=6 and rates['360']>=6)
