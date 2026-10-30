"""Deliberately simple extractive baseline. Never imports reference/adjudication files."""
from .data import Chunk


def generate(question: str, retrieved: list[Chunk], limit: int = 2) -> dict:
    # Authority filter only; no question-specific oracle or reference lookup.
    evidence = [c for c in retrieved if c.current][:limit]
    claims = [{'text':c.text,'citations':[c.passage_id]} for c in evidence]
    return dict(claims=claims,evidence=[c.passage_id for c in evidence],abstain=not evidence)
