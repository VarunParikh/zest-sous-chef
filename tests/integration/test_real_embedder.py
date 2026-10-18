"""Real embedder (ADR-005 default ONNX all-MiniLM-L6-v2). Run with `make test-embedder`.
Relevance is measured by evaluation E5, not asserted here."""
import pytest

from backend.catalogue.store import load_store
from backend.config import load_settings
from backend.retrieval.embedder import default_embedder
from backend.retrieval.retriever import Retriever
from backend.retrieval.vector import VectorStore

pytestmark = pytest.mark.embedder


def test_mood_phrase_without_keywords_still_fills_the_pool(tmp_path):
    store, settings = load_store(), load_settings(env={}, env_file=None)
    vector = VectorStore(tmp_path / "chroma", default_embedder(settings))
    assert vector.ensure(store)
    r = Retriever(store, vector, settings)
    res = r.dishes("beat the summer heat")
    assert not res.lexical_ids  # no keyword match at all
    # with no keyword match the pool is the vector top 20 (Data Model §7), capped by DISH_POOL (25 since C53; was 15)
    from backend.retrieval.retriever import VECTOR_TOP

    assert len(res.hits) == min(settings.dish_pool, VECTOR_TOP) == 20 and not res.fallback_used
