"""Photo flow (US-14 to US-16; FR-50 to 57; ADR-003 v3; Architecture §4.2).

The default provider is the local `qwen3-vl:4b-instruct` (it failed E3; photo accuracy NOT MET).
Gemini is an opt-in behind a consent notice. Sample photos with pre-computed detections are
the demo path and the fallback. Detections are estimates: names are data (screened like
fetched text), resolved in code, and confirmed with one tap before the cart changes.
"""
from __future__ import annotations

import json

from backend.cart import service
from backend.cart.service import CartRuleError
from backend.catalogue.seed import MOCK
from backend.flows.cards import ChoiceOption, Confirm, PhotoConsent, SamplePhoto, SamplePhotos, SuggestionRef, SwapOption, SwapOptions, Undo
from backend.flows.addons import offer_addon
from backend.flows.recipe import resolve
from backend.flows.text import say
from backend.flows.why import drivers, why_card
from backend.llm.client import LLMError
from backend.llm.vision import GeminiVision, OllamaVision, SampleVision

PHOTOS = MOCK / "photos.json"


def sample_list() -> list[dict]:
    photos = json.loads(PHOTOS.read_text())["photos"]
    return [{"id": p["id"], "caption": p["kind"].replace("-", " "), "label": "Sample", "file": p["file"], "split": p["split"],
             "label_status": p.get("label_status", "")} for p in photos]


def samples_card() -> SamplePhotos:
    demo = [p for p in sample_list() if p["split"] == "demo"]
    return SamplePhotos(photos=[SamplePhoto(id=p["id"], caption=p["caption"]) for p in demo])


def make_vision(settings, transport=None, tracer=None, session_id: str = "-"):
    if settings.vision_provider == "ollama":
        return OllamaVision(settings.ollama_base_url, settings.vision_model, settings.timeout_vision_s, transport=transport,
                            num_ctx=settings.vision_num_ctx, tracer=tracer, session_id=session_id)
    if settings.vision_provider == "gemini" and settings.gemini_enabled:
        return GeminiVision(settings.gemini_api_key.get_secret_value(), settings.vision_model, settings.timeout_vision_s,
                            transport=transport, tracer=tracer, session_id=session_id)
    return None


def _offer_samples(session, deps, out, reason: str) -> None:
    out.fallbacks.append("vision")
    deps.tracer.emit("fallback_used", session.session_id, component="vision", reason=reason)
    out.messages.append(say(session, "MSG-PHOTO-SAMPLES", cards=[samples_card()]))


def upload_turn(session, image: bytes, consent: bool, deps, out) -> None:
    """`image` is already validated and stripped (llm.image.prepare_image); it lives only in this call."""
    if consent:
        session.photo_consent = True
    provider = make_vision(deps.settings, deps.vision_transport, deps.tracer, session.session_id)
    if provider is None:
        _offer_samples(session, deps, out, "provider_off")
        return
    if isinstance(provider, GeminiVision) and not session.photo_consent:  # FR-50: nothing leaves before consent
        out.messages.append(say(session, "MSG-PHOTO-CONSENT", cards=[PhotoConsent(notice=_consent_text())]))
        return
    try:
        result = provider.detect(image)
    except LLMError as e:  # timeout, failure or invalid output after the retry: the labelled samples (FR-55)
        _offer_samples(session, deps, out, type(e).__name__)
        return
    finally:
        del image
    detected(session, result, deps, out)


def _consent_text() -> str:
    from backend.flows.templates import TEMPLATES

    return TEMPLATES["MSG-PHOTO-CONSENT"]


def sample_turn(session, photo_id: str, deps, out) -> None:
    detected(session, SampleVision(PHOTOS).detect_sample(photo_id), deps, out)


def detected(session, result, deps, out) -> None:
    if result.quality in ("dark", "blurry"):
        out.messages.append(say(session, "MSG-PHOTO-DARK"))
        return
    if not result.scene_is_food or not result.items:
        out.messages.append(say(session, "MSG-PHOTO-NONE"))
        return
    names = ", ".join(i.name for i in result.items)
    if deps.guard.check(names, source="transcript", session_id=session.session_id).blocked:  # text in an image is data
        out.messages.append(say(session, "MSG-INJECT-DATA"))
        return
    retriever, sure, low = deps.retriever_factory(), [], []
    for item in result.items:
        res = resolve(retriever, item.name, session.session_id)
        if res.kind != "resolved" or res.term in sure or res.term in low:
            continue  # unknown or ambiguous names are left out, never guessed into the cart
        (sure if item.confidence >= deps.settings.confidence_threshold else low).append(res.term)
    if not sure and not low:
        out.messages.append(say(session, "MSG-PHOTO-NONE"))
        return
    state = session.next_id("ph")
    session.pending[state] = {"kind": "photo_state", "sure": sure, "low": list(low), "accepted": []}
    if low:  # MSG-PHOTO-LOW: Yes / No per unsure item
        cards = []
        for term in low:
            cid = session.next_id("c")
            session.pending[cid] = {"kind": "photo_item", "state": state, "term": term}
            cards.append(Confirm(confirm_id=cid, prompt=f"Is there {term}?",
                                 options=[ChoiceOption(value="yes", label="Yes"), ChoiceOption(value="no", label="No")]))
        out.messages.append(say(session, "MSG-PHOTO-LOW", cards=cards, items=", ".join(low)))
        return
    cid = session.next_id("c")
    session.pending[cid] = {"kind": "photo_confirm", "state": state}
    card = Confirm(confirm_id=cid, prompt="Find a dish with these?",
                   options=[ChoiceOption(value="yes", label="Yes"), ChoiceOption(value="no", label="No")])
    out.messages.append(say(session, "MSG-PHOTO-CONFIRM", cards=[card], items=", ".join(sure)))


def answer(session, pending: dict, choice: str, deps, out) -> None:
    """Confirm taps: one per unsure item (MSG-PHOTO-LOW) or the single MSG-PHOTO-CONFIRM."""
    state = session.pending.get(pending["state"])
    if state is None:
        raise CartRuleError("STALE", "That photo question has expired.")
    if pending["kind"] == "photo_confirm":
        del session.pending[pending["state"]]
        if choice == "yes":
            _cart(session, state["sure"], deps, out)
        return
    state["low"].remove(pending["term"])
    if choice == "yes":
        state["accepted"].append(pending["term"])
    if not state["low"]:  # every unsure item answered: the confirmation is complete
        del session.pending[pending["state"]]
        _cart(session, state["sure"] + state["accepted"], deps, out)


def _uses(rec, terms: set[str], store) -> set[str]:
    return {store.lexicon.canonical(i.ingredient_name) or i.ingredient_name for i in rec.ingredients} & terms


def _missing(rec, terms: set[str], store) -> int:
    return sum(1 for i in rec.ingredients if i.essential and (store.lexicon.canonical(i.ingredient_name) or i.ingredient_name) not in terms)


def _cart(session, terms: list[str], deps, out) -> None:
    """FR-53, 54: rank eligible dishes that use the detected items; cart only the top dish's missing items."""
    have = set(terms)
    rec = session.recommend_dishes(" ".join(terms), deps.ctx, deps.store, deps.retriever_factory(), deps.tracer, display=15)
    session.last_recommendation = rec
    ranked = [s for s in rec.scored if s.breakdown.eligible and _uses(deps.store.dish(s.candidate_id), have, deps.store)][:3]
    if not ranked:
        out.messages.append(say(session, "MSG-PHOTO-NONE"))
        return
    top, alts = ranked[0], [s.candidate_id for s in ranked[1:3]]
    try:
        sid, added = service.add_suggested(session, top.candidate_id, alts, "photo", deps.ctx, deps.store,
                                           exclude_terms=frozenset(have))
    except CartRuleError:
        out.messages.append(say(session, "MSG-PHOTO-NONE"))
        return
    store = deps.store
    options = [SwapOption(dish_id=a, name=f"{store.dish(a).dish.name} ({_missing(store.dish(a), have, store)} missing)") for a in alts]
    used = sorted(_uses(store.dish(top.candidate_id), have, store))
    reason = (f"{added.name} uses {len(used)} of the items you have ({', '.join(used)}) and needs {len(added.lines)} more; "
              f"among dishes that use your items it scored highest on {' and '.join(drivers(top.breakdown)[:2]) or 'your settings'}.")
    why = why_card(sid, "photo", reason, top, ranked[1:3], store, used=used)
    out.messages.append(say(session, "MSG-PHOTO-OK", cards=[SwapOptions(suggestion_id=sid, options=options), Undo(suggestion_id=sid), why],
                            items=", ".join(terms), dish=added.name, n=len(added.lines)))
    out.cart_changed = True
    out.suggestions.append(SuggestionRef(suggestion_id=sid, type="dish", candidate_id=top.candidate_id, rank=1))
    deps.tracer.emit("suggestion_shown", session.session_id, suggestion_id=sid, candidate_id=top.candidate_id, alternatives=alts)
    deps.tracer.emit("cart_mutated", session.session_id, action="photo_add", item_count=len(session.cart.lines()))
    offer_addon(session, added, deps, out)
