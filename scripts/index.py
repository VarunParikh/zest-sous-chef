"""Build or refresh the Chroma index (ADR-005; NFR-12). Rebuilds only when the catalogue
hash, the embedder or the Chroma version changed.

Run: .venv/bin/python scripts/index.py
"""
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from backend.catalogue.store import load_store  # noqa: E402
from backend.config import load_settings  # noqa: E402
from backend.retrieval.embedder import default_embedder  # noqa: E402
from backend.retrieval.vector import VectorStore, catalogue_hash  # noqa: E402


def main() -> int:
    settings, store = load_settings(), load_store()
    t0 = time.perf_counter()
    embedder = default_embedder(settings)
    vector = VectorStore(settings.resolve(settings.chroma_path), embedder)
    rebuilt = vector.ensure(store)
    print(f"index {'rebuilt' if rebuilt else 'up to date'}: {len(store.dishes)} dishes, {len(store.variants)} variants, "
          f"embedder {embedder.name}, catalogue {catalogue_hash(store)}, {time.perf_counter() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
