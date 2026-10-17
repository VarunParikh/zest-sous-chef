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


def default_embedder(settings: Settings):
    if settings.embedding_provider == "chroma_default" and not settings.embedding_model:
        return ChromaDefaultEmbedder()
    raise ValueError(f"unsupported embedder {settings.embedding_provider}:{settings.embedding_model} (ADR-005)")
