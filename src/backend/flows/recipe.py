"""Shared carting of extracted ingredient lines (text recipes and videos; FR-13, 30, 90, 112; Agent Design §7.5).

The model only names ingredients. Code resolves each name through the hybrid retriever,
chooses and checks the variant, converts spoon units, and carts it. Ambiguous names get a
question, unknown names are never carted, and a recipe with any blocked item carts nothing.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.engine.variants import choose_variant
from backend.flows.cards import ChoiceOption, Clarify
from backend.session.levers import LeverSet

SPOON_ML = {"tsp": 5.0, "tbsp": 15.0, "cup": 240.0, "pinch": 0.5}  # 1 ml taken as 1 g; always an estimate
DEFAULT_NAME = "Your recipe"


@dataclass
class Item:
    term: str
    qty: float
    unit: str
    estimated: bool
    variant_id: str
    reason: str
    alternatives: list[str] = field(default_factory=list)


@dataclass
class Prepared:
    items: list[Item] = field(default_factory=list)
    blocked: list[tuple[str, tuple[str, ...]]] = field(default_factory=list)  # (name as written, rules)
    ambiguous: list[tuple[object, list[str]]] = field(default_factory=list)  # (line, options)
    unknown: list[str] = field(default_factory=list)


def _singulars(name: str):
    n = name.strip().lower()
    if n.endswith("ies"):
        yield n[:-3] + "y"
        yield n[:-3] + "i"
    if n.endswith("es"):
        yield n[:-2]
    if n.endswith("s"):
        yield n[:-1]


def resolve(retriever, name: str, session_id: str):
    """The retriever's resolution; a plural that resolves to nothing is retried in its singular forms."""
    res = retriever.resolve_ingredient(name, session_id)
    if res.kind == "unknown":
        for s in _singulars(name):
            alt = retriever.resolve_ingredient(s, session_id)
            if alt.kind != "unknown":
                return alt
    return res


def _quantity(qty, unit, estimated, variant_id, store) -> tuple[float, str, bool]:
    skus = store.skus_for(variant_id)
    pack = skus[0].pack if skus else None
    pack_unit = pack.unit.value if pack else "g"
    if qty is None:
        return (pack.qty if pack else 1.0), pack_unit, True
    if unit in SPOON_ML:
        return qty * SPOON_ML[unit], ("ml" if pack_unit in ("ml", "l") else "g"), True
    if unit is None:
        if pack_unit == "piece":
            return qty, "piece", estimated
        return (pack.qty if pack else 1.0), pack_unit, True
    return qty, unit, estimated


def item_for(term: str, qty, unit, estimated, levers: LeverSet, ctx, store) -> Item | tuple[str, tuple[str, ...]]:
    choice = choose_variant(term, levers, ctx, store)
    if choice.chosen is None:
        rules = tuple(sorted({r for _, failed in choice.excluded for r in failed})) or ("not_in_catalogue",)
        return term, rules
    q, u, est = _quantity(qty, unit, estimated, choice.chosen.variant_id, store)
    return Item(term, q, u, est, choice.chosen.variant_id, choice.reason, [v.variant_id for v in choice.alternatives[:3]])


def prepare(session, lines, deps) -> Prepared:
    out, levers = Prepared(), session.snapshot
    retriever = deps.retriever_factory()
    for ln in lines:
        res = resolve(retriever, ln.name, session.session_id)
        if res.kind == "clarify":
            out.ambiguous.append((ln, list(res.options)))
            continue
        if res.kind == "unknown":
            out.unknown.append(ln.name)
            continue
        got = item_for(res.term, ln.qty, ln.unit, ln.estimated, levers, deps.ctx, deps.store)
        if isinstance(got, Item):
            out.items.append(got)
        else:
            out.blocked.append((ln.name, got[1]))
    return out


def setting_label(rules: tuple[str, ...], levers: LeverSet) -> str:
    """Name the user's own setting that removed an item (MSG-PERSONA-BLOCK)."""
    r = rules[0] if rules else ""
    if r.startswith("diet:"):
        return levers.diet
    if r.startswith("faith:"):
        return levers.faith
    if r.startswith("special:"):
        key = r.split(":", 1)[1].replace("_", " ").lower()
        return next((d for d in levers.specialized_diets if key.split()[0] in d.lower()), "diet")
    if r.startswith("allergen:"):
        return f"{r.split(':', 1)[1]} allergy"
    if r in ("stock", "out_of_stock"):
        return "stock filter"
    return "current"


def dish_choice(session, options: list[tuple[str, str]], kind: str = "dish_choice", **extra) -> Clarify:
    qid = session.next_id("q")
    session.pending[qid] = {"kind": kind, "options": [v for v, _ in options], **extra}
    return Clarify(question_id=qid, prompt="Choose a dish", options=[ChoiceOption(value=v, label=label) for v, label in options])


def item_question(session, line, options: list[str], cart_dish_id: str | None, dish_name: str) -> Clarify:
    qid = session.next_id("q")
    session.pending[qid] = {"kind": "ambiguous_item", "options": options, "qty": line.qty, "unit": line.unit,
                            "estimated": line.estimated, "cart_dish_id": cart_dish_id, "dish_name": dish_name}
    return Clarify(question_id=qid, prompt=f"Which {line.name}?", options=[ChoiceOption(value=o, label=o) for o in options])
