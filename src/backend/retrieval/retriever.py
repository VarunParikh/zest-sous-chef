"""Hybrid retriever: BM25 plus vector neighbours, fused by RRF (FR-110 to 113, 117, 118; ADR-004 v2).

Returns candidate IDs with their ranks only. Eligibility and the levers run afterwards
in the engine (G9, FR-112). If the vector store is absent or fails, retrieval falls back
to lexical plus synonyms (and add-ons to the curated list alone) and traces
`fallback_used`; it never raises to the caller (FR-117, NFR-02).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from backend.catalogue.store import Store
from backend.config import Settings, load_settings
from backend.retrieval.documents import dish_lexical_text, term_lexical_texts
from backend.retrieval.fusion import rrf
from backend.retrieval.lexical import LexicalIndex
from backend.retrieval.text import doc_tokens, expand
from backend.retrieval.vector import DISHES, VARIANTS

LEXICAL_TOP = VECTOR_TOP = 20  # Data Model §7.4


@dataclass
class Hit:
    id: str
    fused_score: float
    fused_rank: int
    lexical_rank: int | None = None
    vector_rank: int | None = None
    vector_distance: float | None = None
    curated_rank: int | None = None
    curated_strength: float | None = None


@dataclass
class RetrievalResult:
    kind: str
    hits: list[Hit]
    lexical_ids: list[str] = field(default_factory=list)
    vector_ids: list[str] = field(default_factory=list)
    fallback_used: bool = False
    latency_ms: float = 0.0


@dataclass
class Resolution:
    kind: str  # resolved | clarify | unknown
    term: str | None
    options: list[str] = field(default_factory=list)
    hits: list[Hit] = field(default_factory=list)


class Retriever:
    def __init__(self, store: Store, vector=None, settings: Settings | None = None, tracer=None):
        self.store, self.vector, self.tracer = store, vector, tracer
        self.settings = settings or load_settings()
        self._dish_index = LexicalIndex({r.dish.dish_id: dish_lexical_text(r) for r in store.dishes})
        self._term_docs = term_lexical_texts(store.lexicon, store.synonyms)
        self._term_index = LexicalIndex(self._term_docs)

    # -- plumbing ------------------------------------------------------------
    def _trace(self, event: str, session_id: str, **data):
        if self.tracer is not None:
            self.tracer.emit(event, session_id, **data)

    def _vector_call(self, fn: str, *args, session_id: str) -> tuple[list[dict] | None, bool]:
        """(results, fallback_used). Lexical mode is a deliberate setting, not a fallback."""
        if self.settings.retrieval_mode == "lexical":
            return None, False
        if self.vector is None:
            self._trace("fallback_used", session_id, dependency="vector_store", reason="not configured")
            return None, True
        try:
            return getattr(self.vector, fn)(*args), False
        except Exception as e:  # noqa: BLE001 - any vector failure degrades to lexical (FR-117)
            self._trace("fallback_used", session_id, dependency="vector_store", reason=type(e).__name__)
            return None, True

    @staticmethod
    def _hits(fused, distances: dict[str, float], extra: dict[str, dict] | None = None) -> list[Hit]:
        out = []
        for rank, f in enumerate(fused, start=1):
            h = Hit(f.id, f.score, rank, f.ranks.get("lexical"), f.ranks.get("vector"), distances.get(f.id))
            for k, v in (extra or {}).get(f.id, {}).items():
                setattr(h, k, v)
            if "curated" in f.ranks:
                h.curated_rank = f.ranks["curated"]
            out.append(h)
        return out

    # -- dish and mood lookups -------------------------------------------------
    def dishes(self, query: str, session_id: str = "-") -> RetrievalResult:
        t0 = time.perf_counter()
        lex = [i for i, _ in self._dish_index.search(expand(query, self.store.synonyms), LEXICAL_TOP)]
        vec, fallback = self._vector_call("query", DISHES, query, VECTOR_TOP, session_id=session_id)
        vec_ids = [r["id"].removeprefix("dish:") for r in vec or []]
        dist = {r["id"].removeprefix("dish:"): r["distance"] for r in vec or []}
        fused = rrf({"lexical": lex, "vector": vec_ids}, k=self.settings.rrf_k)[: self.settings.dish_pool]
        res = RetrievalResult("dish", self._hits(fused, dist), lex, vec_ids, fallback, (time.perf_counter() - t0) * 1000)
        self._trace("retrieval_candidates", session_id, kind="dish", lexical_top_ids=lex[:10], vector_top_ids=vec_ids[:10],
                    fused_pool_ids=[h.id for h in res.hits], latency_ms=round(res.latency_ms, 1))
        return res

    # -- ingredient names (FR-13) --------------------------------------------
    def _name_matches(self, word: str) -> list[str]:
        """Terms whose name, alias or synonym equals the word, or whose alias starts with it ("methi dana")."""
        lex, hits = self.store.lexicon, []
        for t, e in lex.entries.items():
            names = [t, *e.aliases]
            if word in names or any(a.startswith(word + " ") for a in e.aliases):
                hits.append(t)
        for s in self.store.synonyms:
            if s["type"] == "ingredient" and s["query_term"].lower() == word:
                t = lex.canonical(s["maps_to"])
                if t and t not in hits:
                    hits.append(t)
        return hits

    def resolve_ingredient(self, name: str, session_id: str = "-") -> Resolution:
        word = " ".join(doc_tokens(name))
        lex = [t for t, _ in self._term_index.search(doc_tokens(name), LEXICAL_TOP)]
        vec, _ = self._vector_call("query", VARIANTS, name, VECTOR_TOP, session_id=session_id)
        vec_terms: list[str] = []
        for r in vec or []:
            term = self.store.lexicon.canonical(self.store.variant(r["id"].removeprefix("var:")).ingredient_list[0])
            if term and term not in vec_terms:
                vec_terms.append(term)
        fused = rrf({"lexical": lex, "vector": vec_terms}, k=self.settings.rrf_k)
        hits = self._hits(fused, {})
        score = {h.id: h.fused_score for h in hits}
        matches = sorted(self._name_matches(word), key=lambda t: (-score.get(t, 0.0), t))
        if len(matches) == 1:
            return Resolution("resolved", matches[0], matches, hits)
        if len(matches) >= 2:
            s1, s2 = score.get(matches[0], 0.0), score.get(matches[1], 0.0)
            if s1 == 0 or (s1 - s2) / s1 < self.settings.ambiguity_margin:
                return Resolution("clarify", None, matches, hits)
            return Resolution("resolved", matches[0], matches, hits)
        if lex:  # a partial lexical match ("toned milk" -> milk)
            top = next(h for h in hits if h.lexical_rank is not None)
            return Resolution("resolved", top.id, [top.id], hits)
        return Resolution("unknown", None, [h.id for h in hits[:3]], hits)
