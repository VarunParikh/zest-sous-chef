import json

import pytest

from backend.catalogue.store import load_store
from backend.config import load_settings
from backend.retrieval.embedder import HashEmbedder
from backend.retrieval.retriever import Retriever
from backend.retrieval.vector import VectorStore
from backend.trace import Tracer


@pytest.fixture(scope="session")
def store():
    return load_store()


@pytest.fixture(scope="session")
def settings():
    return load_settings(env={}, env_file=None)


@pytest.fixture(scope="session")
def vector(tmp_path_factory, store):
    v = VectorStore(tmp_path_factory.mktemp("chroma"), HashEmbedder())
    v.ensure(store)
    return v


@pytest.fixture
def tracer(tmp_path):
    return Tracer(tmp_path / "trace.jsonl")


def events(tracer, name=None):
    if not tracer.path.exists():
        return []
    rows = [json.loads(line) for line in tracer.path.read_text().splitlines()]
    return [r for r in rows if name is None or r["event"] == name]


@pytest.fixture
def retriever(store, vector, settings, tracer):
    return Retriever(store, vector, settings, tracer)


@pytest.fixture
def lexical_only(store, settings, tracer):
    return Retriever(store, None, settings, tracer)


class BrokenVector:
    def query(self, *a, **k):
        raise RuntimeError("vector store down")

    def neighbours(self, *a, **k):
        raise RuntimeError("vector store down")
