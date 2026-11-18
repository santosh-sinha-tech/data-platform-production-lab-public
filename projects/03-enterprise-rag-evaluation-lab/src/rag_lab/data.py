"""Parse synthetic JSON documents; chunk within author-defined atomic passages."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

@dataclass(frozen=True)
class Chunk:
    id: str
    passage_id: str
    document_id: str
    text: str
    current: bool
    start: int
    end: int


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def chunk_documents(documents: list[dict], size: int, overlap: int) -> list[Chunk]:
    if size < 1 or not 0 <= overlap < size:
        raise ValueError('Require size > overlap >= 0')
    result = []
    for doc in documents:
        for passage in doc['passages']:
            words = passage['text'].split()
            for start in range(0, len(words), size-overlap):
                end = min(start+size, len(words))
                text = ' '.join(words[start:end])
                digest = hashlib.sha256(text.encode()).hexdigest()[:12]
                result.append(Chunk(f"{passage['id']}@{start}:{end}:{digest}", passage['id'], doc['id'], text, doc['current'], start, end))
                if end == len(words):
                    break
    return result


def validate(documents: list[dict], references: dict, adjudications: dict, fixtures: dict) -> None:
    doc_ids = [d['id'] for d in documents]
    passages = {p['id']:p['text'] for d in documents for p in d['passages']}
    assert len(doc_ids) == len(set(doc_ids)), 'Duplicate document IDs'
    assert len(passages) == sum(len(d['passages']) for d in documents), 'Duplicate passages'
    questions = references['questions']
    assert len({q['id'] for q in questions}) == len(questions)
    for q in questions:
        assert set(q['relevance']) <= passages.keys()
        assert all(g in (1,2,3) for g in q['relevance'].values())
        assert set(q['expected_facts']) <= adjudications['claims'].keys()
        assert bool(q['expected_facts']) == q['answerable']
    for claim in adjudications['claims'].values():
        assert set(claim['supports']+claim['contradicts']) <= passages.keys()
        assert not set(claim['supports']) & set(claim['contradicts'])
    for fixture in fixtures['answers']:
        assert fixture['question_id'] in {q['id'] for q in questions}
        assert set(fixture['evidence']) <= passages.keys()
        assert not fixture['abstain'] or not fixture['claims']
        for claim in fixture['claims']:
            assert set(claim['citations']) <= passages.keys()
