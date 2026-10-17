"""BM25 lexical index (ADR-004; `rank-bm25`)."""
from __future__ import annotations

from rank_bm25 import BM25Okapi

from backend.retrieval.text import doc_tokens


class LexicalIndex:
    def __init__(self, docs: dict[str, str]):
        self.ids = list(docs)
        self._bm25 = BM25Okapi([doc_tokens(docs[i]) or ["_"] for i in self.ids])

    def search(self, query_tokens: list[str], top: int = 20) -> list[tuple[str, float]]:
        if not query_tokens:
            return []
        scores = self._bm25.get_scores(query_tokens)
        ranked = sorted((s, i) for i, s in zip(self.ids, scores) if s > 0)
        ranked.sort(key=lambda x: (-x[0], x[1]))
        return [(i, float(s)) for s, i in ranked[:top]]
