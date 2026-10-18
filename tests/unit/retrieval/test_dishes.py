"""Hybrid dish retrieval, index, guardrails after retrieval, inspector, fallback
(US-37, US-40; FR-110 to 112, 115, 117; T-040, T-042, T-044 to T-046, T-021)."""
from datetime import datetime

import pytest

from backend.engine.context import build_context
from backend.engine.recommend import recommend_dishes
from backend.retrieval.documents import dish_embedding_text, variant_embedding_text
from backend.retrieval.embedder import HashEmbedder
from backend.retrieval.fusion import rrf
from backend.retrieval.retriever import Retriever
from backend.retrieval.vector import VectorStore
from backend.catalogue.validators import PRICE_OR_STOCK
from tests.unit.engine.conftest import levers
from tests.unit.retrieval.conftest import BrokenVector, events

CTX = build_context(datetime(2026, 10, 17, 19, 0))


def test_t040_rrf_matches_hand_calculation():
    fused = rrf({"lexical": ["x", "y"], "vector": ["z", "y", "x"]}, k=60)
    assert [f.id for f in fused] == ["x", "y", "z"]
    expected = {"x": 1 / 61 + 1 / 63, "y": 1 / 62 + 1 / 62, "z": 1 / 61}
    for f in fused:
        assert f.score == pytest.approx(expected[f.id], abs=1e-12)
    assert fused[0].ranks == {"lexical": 1, "vector": 3}


def test_t044_index_rebuilds_on_catalogue_or_embedder_change(tmp_path, store):
    v = VectorStore(tmp_path / "c", HashEmbedder())
    assert v.ensure(store) is True
    assert v.ensure(store) is False
    changed = store.with_dishes([store.dishes[0].__class__(store.dishes[0].dish.model_copy(update={"description": "changed"}), store.dishes[0].ingredients)] + store.dishes[1:])
    assert v.ensure(changed) is True
    other = VectorStore(tmp_path / "c", HashEmbedder(dim=128))
    assert other.ensure(changed) is True


def test_t045_embedding_texts_have_no_price_or_stock(store):
    for rec in store.dishes:
        assert not PRICE_OR_STOCK.search(dish_embedding_text(rec))
    for v in store.variants:
        assert not PRICE_OR_STOCK.search(variant_embedding_text(v))


def test_mood_query_gives_the_configured_pool(retriever, tracer, settings):
    res = retriever.dishes("something cooling")
    assert len(res.hits) == settings.dish_pool == 25 and not res.fallback_used  # pool 25 since C53 (was 15)
    ids = [h.id for h in res.hits]
    # every keyword hit carries the mood; which cooling dishes fill the pool (and AC-35's
    # "Chaas and Sweet Lassi appear") is measured by evaluation E5 with the real embedder (Test Plan §5)
    lexical = [h.id for h in res.hits if h.lexical_rank is not None]
    assert lexical and all("cooling" in retriever.store.dish(i).dish.mood_tags for i in lexical)
    [ev] = events(tracer, "retrieval_candidates")
    assert ev["data"]["kind"] == "dish" and ev["data"]["fused_pool_ids"] == ids


def test_vector_returns_ids_only(vector):
    for hit in vector.query("zest_dishes", "creamy paneer", 5):
        assert set(hit) == {"id", "distance"}


def test_t021_vector_candidate_breaking_persona_removed_and_traced(store, retriever, tracer):
    rec = recommend_dishes("garlic bread", levers(diet="Jain (No Root Veggies / Pure Veg)", faith="Jain (Strict Root-Free)"),
                           CTX, store, retriever, tracer)
    pool = {h.id: h for h in rec.pool}
    assert "D32" in pool and pool["D32"].vector_rank is not None
    assert "D32" not in [s.candidate_id for s in rec.shown]
    filtered = [e for e in events(tracer, "guardrail_filtered") if e["data"]["candidate_id"] == "D32"]
    assert filtered and filtered[0]["data"]["rules_failed"]


def test_t046_inspector_lists_retrieval_and_scores(store, retriever, tracer):
    rec = recommend_dishes("feeling indulgent", levers(), CTX, store, retriever, tracer)
    assert len(rec.inspector) == len(rec.pool) >= 15 and len(rec.shown) == 3
    for row in rec.inspector:
        assert {"candidate_id", "lexical_rank", "vector_rank", "vector_distance", "fused_rank", "fused_score",
                "eligible", "filtered_by", "final"} <= set(row)
        if not row["eligible"]:
            assert row["filtered_by"] and row["final"] == 0


def test_levers_reorder_the_shown_set(store, retriever):
    a = recommend_dishes("feeling indulgent", levers(history={"desserts": 0.0}, weights={"purchase_history": 1.0}), CTX, store, retriever)
    b = recommend_dishes("feeling indulgent", levers(history={"desserts": 1.0}, weights={"purchase_history": 1.0}), CTX, store, retriever)
    assert [s.candidate_id for s in a.shown] != [s.candidate_id for s in b.shown]


@pytest.mark.parametrize("vector", [None, BrokenVector()], ids=["absent", "broken"])
def test_t042_vector_down_falls_back_to_lexical(store, settings, tracer, vector):
    r = Retriever(store, vector, settings, tracer)
    res = r.dishes("paneer butter masala")
    assert res.fallback_used and res.hits and {h.id for h in res.hits[:2]} == {"D06", "D130"}  # PBM and its Jain variant
    assert all(h.vector_rank is None for h in res.hits)
    [ev] = events(tracer, "fallback_used")
    assert ev["data"]["dependency"] == "vector_store"


def test_lexical_mode_never_queries_vector(store, tracer):
    from backend.config import load_settings

    r = Retriever(store, BrokenVector(), load_settings(env={"RETRIEVAL_MODE": "lexical"}, env_file=None), tracer)
    res = r.dishes("paneer butter masala")
    assert res.hits and not events(tracer, "fallback_used")


def test_ollama_embedder_calls_embed_api():
    import json as _json

    import httpx

    from backend.retrieval.embedder import OllamaEmbedder, default_embedder
    from backend.config import load_settings

    seen = []

    def handler(req):
        body = _json.loads(req.content)
        seen.append((req.url.path, body))
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2, 0.3] for _ in body["input"]]})

    e = OllamaEmbedder("http://127.0.0.1:11434", "nomic-embed-text", transport=httpx.MockTransport(handler))
    assert e.name == "ollama:nomic-embed-text"
    assert e(["a", "b"]) == [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]
    assert seen[0][0] == "/api/embed" and seen[0][1] == {"model": "nomic-embed-text", "input": ["a", "b"]}
    s = load_settings(env={"EMBEDDING_PROVIDER": "ollama", "EMBEDDING_MODEL": "nomic-embed-text"}, env_file=None)
    assert isinstance(default_embedder(s), OllamaEmbedder)


def test_ollama_embedder_batches_large_inputs():
    import json as _json

    import httpx

    from backend.retrieval.embedder import OllamaEmbedder

    sizes = []

    def handler(req):
        n = len(_json.loads(req.content)["input"])
        sizes.append(n)
        return httpx.Response(200, json={"embeddings": [[1.0] for _ in range(n)]})

    out = OllamaEmbedder("http://x.test", "m", transport=httpx.MockTransport(handler))(["t"] * 150)
    assert len(out) == 150 and max(sizes) <= 64 and sum(sizes) == 150


def test_t044_interrupted_build_is_rebuilt(tmp_path, store):
    """A build that crashes half-way must not look up to date on the next run."""

    class Flaky(HashEmbedder):
        calls = 0

        def __call__(self, texts):
            Flaky.calls += 1
            if Flaky.calls == 2:
                raise RuntimeError("embedder crashed mid-build")
            return super().__call__(texts)

    v = VectorStore(tmp_path / "c", Flaky())
    with pytest.raises(RuntimeError):
        v.ensure(store)
    fresh = VectorStore(tmp_path / "c", HashEmbedder())  # same name as Flaky: hash-bow-256
    assert fresh.ensure(store) is True
    assert len(fresh.query("zest_variants", "skimmed milk", 5)) == 5
