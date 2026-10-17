"""Embedded Chroma vector store (ADR-005; FR-112; NFR-12).

Returns IDs and distances only. Embeddings are computed by our embedder and passed in,
so the collections hold no embedding-function config. Collection metadata records the
embedder, the Chroma version and a hash of the embedded texts; a mismatch rebuilds.
Chroma's anonymised telemetry is switched off.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from backend.catalogue.store import Store
from backend.retrieval.documents import dish_embedding_text, variant_embedding_text

DISHES, VARIANTS = "zest_dishes", "zest_variants"


class VectorUnavailable(RuntimeError):
    pass


def _docs(store: Store) -> dict[str, dict[str, str]]:
    return {
        DISHES: {f"dish:{r.dish.dish_id}": dish_embedding_text(r) for r in store.dishes},
        VARIANTS: {f"var:{v.variant_id}": variant_embedding_text(v) for v in store.variants},
    }


def catalogue_hash(store: Store) -> str:
    h = hashlib.sha256()
    for name, docs in sorted(_docs(store).items()):
        for i in sorted(docs):
            h.update(f"{name}|{i}|{docs[i]}\n".encode())
    return h.hexdigest()[:16]


class VectorStore:
    def __init__(self, path: Path, embedder):
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        self.path = Path(path)
        self.embedder = embedder
        self._chroma_version = chromadb.__version__
        self._client = chromadb.PersistentClient(path=str(self.path), settings=ChromaSettings(anonymized_telemetry=False))

    def _meta(self, digest: str) -> dict:
        return {"hnsw:space": "cosine", "embedder": self.embedder.name, "chroma": self._chroma_version, "catalogue": digest}

    def ensure(self, store: Store) -> bool:
        """Build the collections if missing or stale. Returns True when it (re)built."""
        digest = catalogue_hash(store)
        want = self._meta(digest)
        current = {c.name: c for c in self._client.list_collections()}
        if all(n in current and {k: current[n].metadata.get(k) for k in want} == want for n in (DISHES, VARIANTS)):
            return False
        for name, docs in _docs(store).items():
            if name in current:
                self._client.delete_collection(name)
            col = self._client.create_collection(name, metadata=want)
            ids = sorted(docs)
            for start in range(0, len(ids), 500):
                batch = ids[start:start + 500]
                col.add(ids=batch, embeddings=self.embedder([docs[i] for i in batch]),
                        metadatas=[{"kind": name} for _ in batch])
        return True

    def query(self, collection: str, text: str, n: int) -> list[dict]:
        col = self._client.get_collection(collection)
        res = col.query(query_embeddings=self.embedder([text]), n_results=n, include=["distances"])
        return [{"id": i, "distance": float(d)} for i, d in zip(res["ids"][0], res["distances"][0])]

    def neighbours(self, dish_id: str, n: int) -> list[dict]:
        """Nearest dishes to a dish's stored embedding (no new embedding is computed)."""
        col = self._client.get_collection(DISHES)
        got = col.get(ids=[f"dish:{dish_id}"], include=["embeddings"])
        if not len(got["ids"]):
            return []
        res = col.query(query_embeddings=[list(got["embeddings"][0])], n_results=n + 1, include=["distances"])
        return [{"id": i, "distance": float(d)} for i, d in zip(res["ids"][0], res["distances"][0]) if i != f"dish:{dish_id}"][:n]
