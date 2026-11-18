"""Exact structured synthetic fact evaluation; no natural-language fact checking."""
from typing import Any

def evaluate(case: dict[str, Any]) -> dict[str, bool]:
    abstained = case['abstained']
    correctness = (case['should_abstain'] if abstained else case['claim'] == case['reference'])
    grounded = abstained or (case['claim'] in case['evidence'] and case['fresh'] and not case['conflict'])
    citation = abstained or (bool(case['citation']) and case['citation'] == case['valid_citation'] and grounded)
    abstention = abstained == case['should_abstain']
    return dict(correct=correctness, grounded=grounded, citation=citation,
                abstention=abstention, passed=correctness and grounded and citation and abstention)
