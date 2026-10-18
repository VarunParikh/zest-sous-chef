"""YouTube flow (US-08 to US-10; FR-12, 20 to 24). The transcript is data: guarded as fetched text,
spotlighted for the model, and it never changes the cart by itself."""
from __future__ import annotations

from backend.cart.allocation import allocate
from backend.flows.cards import ChoiceOption, Confirm, Undo
from backend.flows.text import add_stored, cart_recipe, extract, say, stored_dish
from backend.llm.client import LLMError
from backend.transcripts.source import TranscriptUnavailable, video_id

STAPLE_CATEGORIES = {"spices", "oils"}
STAPLE_TERMS = {"salt", "sugar", "ghee", "oil"}


def _confirm(session, kind: str, options, **extra) -> Confirm:
    cid = session.next_id("c")
    session.pending[cid] = {"kind": kind, **extra}
    return Confirm(confirm_id=cid, prompt="", options=[ChoiceOption(value=v, label=label) for v, label in options])


def youtube_turn(session, text: str, deps, out, force: bool = False) -> None:
    vid = video_id(text)
    if vid is None:  # FR-24: any other URL; nothing is fetched
        out.messages.append(say(session, "MSG-YT-BAD-URL"))
        return
    session.open_dish_id = None  # a link closes the open text dish (FR-30)
    carted = session.videos.get(vid)
    dish = next((d for d in session.cart.dishes if d.cart_dish_id == carted), None)
    if dish is not None and not force:
        card = _confirm(session, "dup_video", (("yes", "Yes"), ("no", "No")), video_id=vid)
        card.prompt = f"Add {dish.name} again?"
        out.messages.append(say(session, "MSG-YT-DUP", cards=[card], dish=dish.name))
        return
    try:
        t = deps.transcripts.fetch(vid)
    except TranscriptUnavailable:
        out.messages.append(say(session, "MSG-YT-PASTE"))
        return
    verdict = deps.guard.check(t.text, source="transcript", session_id=session.session_id)
    if verdict.blocked:  # FR-12: instructions inside fetched text are ignored; nothing is carted
        out.messages.append(say(session, "MSG-INJECT-DATA"))
        return
    try:
        ex = extract(deps, t.text)
    except LLMError:  # invalid after the retry, or timed out: the defined fallback, never a success message
        out.messages.append(say(session, "MSG-YT-PASTE"))
        return
    if t.source == "title":
        rec = stored_dish(deps.store, ex.dish_name)
        if rec is None:
            out.messages.append(say(session, "MSG-YT-PASTE"))
            return
        out.messages.append(say(session, "MSG-YT-TITLE"))
        add_stored(session, rec.dish.dish_id, deps, out, source="youtube")
        added = next((d for d in reversed(session.cart.dishes) if d.dish_id == rec.dish.dish_id), None)
        if added is not None:
            session.videos[vid] = added.cart_dish_id
        return
    if not ex.ingredients:  # FR-22: no recipe in the video
        out.messages.append(say(session, "MSG-YT-NONFOOD"))
        return
    prior = list(session.cart.dishes)
    if t.source == "fixture":
        out.messages.append(say(session, "MSG-YT-FIXTURE"))
    res = cart_recipe(session, ex.dish_name, ex.ingredients, "youtube", deps, out, keep_open=False,
                      headline=lambda d, n: ("MSG-YT-OK", {"dish": d.name, "n": n}))
    if res and res[0] is not None:
        session.videos[vid] = res[0].cart_dish_id
        _pantry(session, res[0], prior, deps, out)


def _is_staple(line, store) -> bool:
    return line.ingredient_name in STAPLE_TERMS or store.variant(line.variant_id).category in STAPLE_CATEGORIES


def _pantry(session, dish, prior, deps, out) -> None:
    """FR-23: after a second link, ask about staples both dishes use (packs are already shared by allocation)."""
    earlier = {ln.ingredient_name for d in prior for ln in d.lines}
    staples = sorted({ln.ingredient_name for ln in dish.lines if ln.ingredient_name in earlier and _is_staple(ln, deps.store)})
    if not staples:
        return
    card = _confirm(session, "pantry", (("have", "Yes, I have them"), ("add", "No, add them")), terms=staples)
    card.prompt = "Already have them at home?"
    out.messages.append(say(session, "MSG-PANTRY", cards=[card], staples=", ".join(staples)))


def answer(session, pending: dict, choice: str, deps, out) -> None:
    """Confirm taps for this flow: a repeated video (MSG-YT-DUP) and the pantry question (MSG-PANTRY)."""
    if pending["kind"] == "dup_video":
        if choice == "yes":
            youtube_turn(session, f"https://youtu.be/{pending['video_id']}", deps, out, force=True)
        return
    if choice != "have":
        return
    prior = session.cart.model_copy(deep=True)
    cart = session.cart.model_copy(deep=True)
    terms = set(pending["terms"])
    for d in cart.dishes:
        d.lines = [ln for ln in d.lines if ln.ingredient_name not in terms]
    cart.dishes = [d for d in cart.dishes if d.lines]
    session.cart = allocate(cart, deps.store)
    sid = session.next_id("sg")
    session.undo_stack.append({"suggestion_id": sid, "kind": "replace", "prior": prior, "dish_name": None})
    out.cart_changed = True
    out.messages.append(say(session, "MSG-EDIT-OK", cards=[Undo(suggestion_id=sid)], change=f"Removed {', '.join(pending['terms'])}"))
