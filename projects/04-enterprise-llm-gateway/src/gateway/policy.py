"""Pure routing/cost policy; no I/O or provider invocation."""

from .store import Denied


def cost(tokens, price):
    """Round integer micro-USD upward, without floating-point money."""
    return (tokens * price + 999999) // 1000000


def routes(body, policy, models):
    total = body.input_tokens + body.max_output_tokens
    preferred = body.model or ("quality" if body.capability == "quality" else "economy")
    if preferred not in policy["models"] or preferred not in models:
        raise Denied("model_forbidden")
    candidates = [preferred] + (
        ["fallback"] if body.allow_fallback and preferred != "fallback" else []
    )
    candidates = [
        m
        for m in candidates
        if m in policy["models"]
        and m in models
        and models[m].get("available", True)
        and (body.capability == "basic" or models[m]["capability"] == "quality")
        and cost(total, models[m]["price"]) <= body.cost_ceiling
    ]
    if not candidates:
        raise Denied("no_permitted_route")
    return (
        preferred,
        candidates,
        max(cost(total, models[m]["price"]) for m in candidates),
    )
