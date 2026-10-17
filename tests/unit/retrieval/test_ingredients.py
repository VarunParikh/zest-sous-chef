"""Regional names and ambiguity (US-06; FR-13; AC-17; T-041, T-043; T-042 ingredient part)."""
import pytest


@pytest.mark.parametrize("which", ["retriever", "lexical_only"])
def test_t041_regional_names_resolve(request, which):
    r = request.getfixturevalue(which)
    for name, term in [("kothmir", "coriander leaves"), ("kandha", "onion"), ("batata", "potato")]:
        res = r.resolve_ingredient(name)
        assert res.kind == "resolved" and res.term == term, (name, res)


def test_t043_ambiguous_name_asks_and_resolves_nothing(retriever):
    res = retriever.resolve_ingredient("methi")
    assert res.kind == "clarify" and res.term is None
    assert set(res.options[:2]) == {"fenugreek leaves", "fenugreek seeds"}


def test_plain_names_are_not_ambiguous(retriever):
    for name in ("milk", "paneer", "tomato", "basmati rice"):
        res = retriever.resolve_ingredient(name)
        assert res.kind == "resolved" and res.term == name, (name, res)


def test_unknown_name(lexical_only):
    assert lexical_only.resolve_ingredient("unobtainium").kind == "unknown"
