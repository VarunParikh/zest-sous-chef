"""Embedders (ADR-005). Default: Chroma's local ONNX all-MiniLM-L6-v2, downloaded once
into the git-ignored `data/models/` (SHA-256 checked by Chroma). Tests use HashEmbedder,
a deterministic bag-of-words hash, so `make test` needs no model (Test Plan principle 3)."""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

from backend.config import REPO_ROOT, Settings
from backend.retrieval.text import doc_tokens

MODELS = REPO_ROOT / "data" / "models"


class HashEmbedder:
    def __init__(self, dim: int = 256):
        self.dim = dim
        self.name = f"hash-bow-{dim}"

    def __call__(self, texts: list[str]) -> list[list[float]]:
        out = []
        for t in texts:
            vec = [0.0] * self.dim
            for tok in doc_tokens(t):
                h = int.from_bytes(hashlib.sha1(tok.encode()).digest()[:4], "big")
                vec[h % self.dim] += 1.0
            norm = math.sqrt(sum(x * x for x in vec)) or 1.0
            out.append([x / norm for x in vec])
        return out


class ChromaDefaultEmbedder:
    def __init__(self, models_dir: Path = MODELS):
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

        ONNXMiniLM_L6_V2.DOWNLOAD_PATH = models_dir / ONNXMiniLM_L6_V2.MODEL_NAME
        self._fn = ONNXMiniLM_L6_V2()
        self.name = f"chroma_default:{ONNXMiniLM_L6_V2.MODEL_NAME}"

    def __call__(self, texts: list[str]) -> list[list[float]]:
        return [list(map(float, v)) for v in self._fn(texts)]


class OllamaEmbedder:
    """An Ollama embedding model via `/api/embed` (ADR-005 comparison arm). Texts are sent
    without task prefixes, the same as for the default embedder."""

    def __init__(self, base_url: str, model: str, timeout_s: float = 60, transport=None):
        import httpx

        self.base_url, self.model = base_url.rstrip("/"), model
        self._http = httpx.Client(transport=transport, timeout=timeout_s)
        self.name = f"ollama:{model}"

    BATCH = 64  # Ollama 0.40.5's runner failed on a 500-text batch ("tokenize: EOF"); 250 worked

    def __call__(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for start in range(0, len(texts), self.BATCH):
            r = self._http.post(f"{self.base_url}/api/embed", json={"model": self.model, "input": texts[start:start + self.BATCH]})
            r.raise_for_status()
            out += [list(map(float, v)) for v in r.json()["embeddings"]]
        return out


def default_embedder(settings: Settings):
    if settings.embedding_provider == "chroma_default" and not settings.embedding_model:
        return ChromaDefaultEmbedder()
    if settings.embedding_provider == "ollama" and settings.embedding_model:
        return OllamaEmbedder(settings.ollama_base_url, settings.embedding_model)
    raise ValueError(f"unsupported embedder {settings.embedding_provider}:{settings.embedding_model} (ADR-005)")
