"""Texts for the lexical index and the embedder (Data Model §7.2).

Price, stock, pack size, brand and diet tags never enter these texts (Data Model §1.2,
V11): eligibility is decided in code from the catalogue, never by similarity.
"""
from __future__ import annotations

from backend.catalogue.models import Variant
from backend.catalogue.seed import DishRecord, Lexicon


def dish_embedding_text(rec: DishRecord) -> str:
    """Dish template: name, course, cuisine, moods, taste, top 6 essential ingredients, aliases, description."""
    d = rec.dish
    top = [i.ingredient_name for i in rec.ingredients if i.essential][:6]
    text = (f"{d.name}. {d.course} from {d.cuisine} cuisine. Mood and occasion: {', '.join(d.mood_tags)}. "
            f"Taste: {', '.join(d.flavour)}. Main ingredients: {', '.join(top)}.")
    if d.aliases:
        text += f" Also called: {', '.join(d.aliases)}."
    return f"{text} {d.description}"


def variant_embedding_text(v: Variant) -> str:
    return v.embedding_text  # built by the generator from the §7.2 variant template


def variant_lexical_text(v: Variant) -> str:
    """Name, ingredient list (qualifiers included) and attribute words; no price, stock or brand."""
    return " ".join([v.name, *v.ingredient_list, v.attributes.get("variant", ""), v.attributes.get("qualifiers", "")])


def dish_lexical_text(rec: DishRecord) -> str:
    d = rec.dish
    words = [d.name, *d.aliases, d.course, d.cuisine, *d.mood_tags, *d.flavour, *(i.ingredient_name for i in rec.ingredients)]
    return " ".join(words)


def term_lexical_texts(lexicon: Lexicon, synonyms: list[dict]) -> dict[str, str]:
    """One lexical document per ingredient term: the term, its aliases and the synonym-table names for it."""
    docs = {t: " ".join([t, *e.aliases]) for t, e in lexicon.entries.items()}
    for s in synonyms:
        if s["type"] == "ingredient":
            term = lexicon.canonical(s["maps_to"])
            if term:
                docs[term] += " " + s["query_term"]
    return docs
