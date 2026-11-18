"""Local BM25, normalized exact dense search, and reciprocal rank fusion."""
import math
import re
from collections import Counter
from .data import Chunk

MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
REVISION = 'c9745ed1d9f207416be6d2e6f8de32d1f16199bf'

def tokens(text: str) -> list[str]:
    return re.findall(r'[a-z0-9_]+', text.lower())


def fuse(rankings: list[list[str]], constant: int = 60) -> list[str]:
    if constant < 1:
        raise ValueError('RRF constant must be positive')
    scores: dict[str,float] = {}
    for ranking in rankings:
        for rank, key in enumerate(dict.fromkeys(ranking), 1):
            scores[key] = scores.get(key, 0) + 1/(constant+rank)
    return sorted(scores, key=lambda key: (-scores[key], key))


class Index:
    def __init__(self, chunks: list[Chunk], backend: str = 'bm25', lexical_fallback: bool = False):
        if not chunks or len({c.id for c in chunks}) != len(chunks):
            raise ValueError('Index requires nonempty unique chunks')
        self.chunks = chunks
        self.backend = backend
        self.by_id = {c.id:c for c in chunks}
        self.corpus = [tokens(c.text) for c in chunks]
        self.lexical_fallback = lexical_fallback
        if lexical_fallback:
            self.counts = [Counter(t) for t in self.corpus]
            self.avgdl = sum(map(len,self.corpus))/len(chunks)
            self.df = Counter(t for row in self.corpus for t in set(row))
        else:
            try:
                from rank_bm25 import BM25Okapi
            except ImportError as exc:
                raise RuntimeError('rank-bm25 unavailable. Install project dependencies or explicitly use --lexical-only --local-bm25. No retrieval method was silently substituted.') from exc
            self.bm25 = BM25Okapi(self.corpus)
        if backend == 'all':
            try:
                import numpy as np
                from sentence_transformers import SentenceTransformer
                self.np = np
                self.model = SentenceTransformer(MODEL, revision=REVISION, device='cpu', trust_remote_code=False, model_kwargs={'use_safetensors': True})
                self.model.max_seq_length = 256
                self.vectors = self.model.encode([c.text for c in chunks],normalize_embeddings=True,convert_to_numpy=True)
                if self.vectors.shape != (len(chunks),384):
                    raise ValueError('Unexpected embedding/index shape')
            except (ImportError, OSError) as exc:
                raise RuntimeError('Dense model unavailable. Install locked dependencies/download pinned model, or explicitly choose --lexical-only. No dense results were produced.') from exc

    def lexical(self, query: str) -> list[str]:
        if not self.lexical_fallback:
            scores = self.bm25.get_scores(tokens(query)).tolist()
        else:
            # Explicit emergency local BM25 variant: positive Robertson IDF, k1=1.5, b=.75.
            scores = []
            for row, counts in zip(self.corpus,self.counts):
                score = 0.0
                for term in tokens(query):
                    freq = counts[term]
                    idf = math.log(1+(len(self.chunks)-self.df[term]+.5)/(self.df[term]+.5))
                    score += idf*freq*2.5/(freq+1.5*(.25+.75*len(row)/self.avgdl))
                scores.append(score)
        return [self.chunks[i].id for i in sorted(range(len(scores)),key=lambda i:(-scores[i],self.chunks[i].id))]

    def dense_ids(self, query: str) -> list[str]:
        vector = self.model.encode([query],normalize_embeddings=True,convert_to_numpy=True)[0]
        scores = self.vectors @ vector
        return [self.chunks[i].id for i in sorted(range(len(scores)),key=lambda i:(-float(scores[i]),self.chunks[i].id))]

    def search(self, query: str, method: str, k: int, constant: int = 60) -> list[Chunk]:
        if k < 1:
            raise ValueError('K must be positive')
        if method in ('bm25','bm25_local'):
            ids = self.lexical(query)
        elif method == 'dense':
            ids = self.dense_ids(query)
        elif method == 'hybrid':
            ids = fuse([self.lexical(query),self.dense_ids(query)],constant)
        else:
            raise ValueError(f'Unknown retrieval method {method}')
        # Passage retrieval: collapse chunk siblings before applying K. Scores use passage qrels.
        selected, seen = [], set()
        for key in ids:
            chunk = self.by_id[key]
            if chunk.passage_id not in seen:
                selected.append(chunk)
                seen.add(chunk.passage_id)
            if len(selected) == k:
                break
        return selected
