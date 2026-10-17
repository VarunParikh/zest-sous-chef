import pytest

from backend.catalogue.store import load_store
from backend.catalogue.seed import load_personas
from backend.session.levers import LeverSet, merge_levers


@pytest.fixture(scope="session")
def store():
    return load_store()


@pytest.fixture(scope="session")
def personas():
    data = load_personas()
    out = {"defaults": LeverSet.model_validate(data["defaults"])}
    for p in data["personas"]:
        out[p["id"]] = LeverSet.model_validate(merge_levers(data["defaults"], p["levers"]))
    return out


def levers(**over):
    """A LeverSet from defaults with nested overrides, e.g. levers(diet=..., business={"stock_filter": False})."""
    base = LeverSet().model_dump()
    return LeverSet.model_validate(merge_levers(base, over))
