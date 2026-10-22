"""Zest 2.0 onboarding (US-42 to US-47) in the built frontend, fake model, real backend, as E2E-001."""
import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def _open(page: Page, app_url: str):
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto(app_url)
    expect(page.get_by_text("Hey there! I'm Zest")).to_be_visible()


def _send(page: Page, text: str):
    page.get_by_label("Message Zest").fill(text)
    page.get_by_label("Message Zest").press("Enter")
    expect(page.get_by_label("Message Zest")).to_be_enabled(timeout=15000)


def test_t124_help_card_examples_act_on_one_tap(page: Page, app_url: str):
    _open(page, app_url)
    _send(page, "what can I say?")
    card = page.get_by_test_id("help-card").last
    expect(card).to_be_visible()
    for label in ["A YouTube recipe", "A dish or recipe", "A mood", "A fridge photo"]:
        expect(card.get_by_role("button", name=re.compile(label))).to_be_visible()
    card.get_by_role("button", name=re.compile("A mood")).click()
    expect(page.get_by_text(re.compile("Let's go with"))).to_be_visible(timeout=15000)
    expect(page.locator("button[aria-label^='Open cart']")).to_be_enabled()


def test_t124_starter_chips_send_on_one_tap(page: Page, app_url: str):
    _open(page, app_url)
    page.get_by_role("button", name="Text recipe").click()
    expect(page.get_by_text("Kadai paneer: 250 g paneer, 2 capsicum and 1 onion")).to_be_visible()  # sent, not pre-filled
    expect(page.get_by_label("Message Zest")).to_have_value("")


def _expand_all(page: Page):
    panel = page.get_by_label("Recommendation levers")
    closed = panel.locator("h3 > button[aria-expanded='false']")
    while closed.count():
        closed.first.click()
    return panel


def test_t121_every_lever_has_a_tooltip_and_a_tag(page: Page, app_url: str):
    _open(page, app_url)
    panel = _expand_all(page)
    controls = panel.evaluate("""el => [...el.querySelectorAll("input[type=range], select, input[role=switch], fieldset")]
        .map(c => {
          const tip = document.getElementById(c.getAttribute('aria-describedby') || '');
          const box = c.closest('div, label, fieldset');
          const tag = (c.tagName === 'FIELDSET' ? c : box)?.querySelector('[data-lever-tag]')?.getAttribute('data-lever-tag')
                      || c.parentElement?.parentElement?.querySelector('[data-lever-tag]')?.getAttribute('data-lever-tag');
          return {name: c.id, tip: tip ? tip.textContent : null, tag: tag || null};
        })""")
    assert len(controls) >= 17  # 4 weights, 3 selects, diets, 2 style, 5 history, 2 trends, price cap, stock switch
    missing = [c for c in controls if not c["tip"] or not c["tag"]]
    assert not missing, missing
    rules = [c for c in controls if c["tag"] == "Rule"]
    assert len(rules) == 5 and all(("removed" in c["tip"]) or ("never" in c["tip"]) for c in rules)


def test_t121_every_specialised_diet_has_an_icon(page: Page, app_url: str):
    _open(page, app_url)
    panel = _expand_all(page)
    diets = ["Standard / Balanced", "Keto Diet", "Intermittent Fasting / Low-GI", "Vegan", "Gluten-Free", "High-Protein Fitness"]
    for d in diets:
        expect(panel.locator(f"[data-diet-icon='{d}']")).to_have_count(1)


def test_t121_tooltip_opens_on_focus_and_closes_with_escape(page: Page, app_url: str):
    _open(page, app_url)
    tip_button = page.get_by_role("button", name="About Dietary Preference")
    tip_button.focus()
    tip = page.get_by_role("tooltip").filter(has_text="removed before ranking").first
    expect(tip).to_be_visible()
    tip_button.press("Escape")
    expect(tip).to_be_hidden()


def test_t120_persona_card_selects_its_preset(page: Page, app_url: str):
    _open(page, app_url)
    meera = page.get_by_role("radio", name=re.compile("Meera Shah"))
    expect(meera).to_contain_text("Jain: no root vegetables, onion, garlic or mushrooms")
    expect(meera.locator("svg[data-avatar='bowl']")).to_have_count(1)  # a cartoon chef with a prop from her levers
    page.get_by_role("button", name=re.compile("Show all")).click()
    expect(page.get_by_role("radio", name=re.compile("Alex"))).to_have_count(0)  # the reviewer persona is not offered (C81)
    cards = page.get_by_role("radio")
    expect(cards).to_have_count(10)
    for i in range(10):
        expect(cards.nth(i).locator("svg[data-avatar]")).to_have_count(1)
    meera.click()
    expect(meera).to_have_attribute("aria-checked", "true")
    expect(page.get_by_text("Changes apply from your next chat session.")).to_be_visible()
    page.get_by_role("button", name="Start new chat").click()
    expect(page.get_by_text("Persona: Meera Shah")).to_be_visible()
    # The cards are a radio group: an arrow key moves to and selects the next persona
    meera.press("ArrowRight")
    expect(meera).to_have_attribute("aria-checked", "false")
    expect(page.get_by_role("radio", checked=True)).to_have_count(1)


MOOD = "I am feeling indulgent"


def _carted_mood(page: Page, app_url: str):
    _open(page, app_url)
    _send(page, MOOD)
    expect(page.get_by_text(re.compile("Let's go with"))).to_be_visible(timeout=15000)
    page.get_by_role("radio", name=re.compile("Meera Shah")).click()
    return page.get_by_role("button", name=f"Apply and rerun “{MOOD}”")


def test_t117_apply_and_rerun_shows_before_and_now(page: Page, app_url: str):
    apply = _carted_mood(page, app_url)
    apply.click()
    dialog = page.get_by_role("alertdialog")
    expect(dialog).to_contain_text("empties your cart")
    dialog.get_by_role("button", name="Apply and rerun").click()
    expect(page.get_by_text("Persona: Meera Shah")).to_be_visible(timeout=15000)
    expect(page.get_by_text(re.compile(r"^(Before: .+ → Now: .+|Same pick.+)$"))).to_be_visible(timeout=15000)
    expect(page.get_by_text(MOOD, exact=True)).to_have_count(1)  # the new chat holds the resent request only
    expect(page.get_by_text("Changes apply from your next chat session.")).to_be_hidden()


def test_t118_cancel_keeps_the_cart_and_the_session(page: Page, app_url: str):
    apply = _carted_mood(page, app_url)
    cart = page.locator("button[aria-label^='Open cart']")
    label = cart.get_attribute("aria-label")
    apply.click()
    dialog = page.get_by_role("alertdialog")
    expect(dialog).to_contain_text(re.compile(r"empties your cart \(\d+ items, ₹[\d,]+\)"))
    dialog.get_by_role("button", name="Cancel").click()
    expect(dialog).to_be_hidden()
    expect(cart).to_have_attribute("aria-label", label)
    expect(page.get_by_text("Persona: Jordan Fernandes (control)")).to_be_visible()
    expect(page.get_by_text(re.compile("^Before: |^Same pick"))).to_have_count(0)


def test_t117_photo_requests_get_the_right_apply_button(page: Page, app_url: str, tmp_path):
    """AC-48: a sample photo is rerun as that sample; an uploaded photo is never stored, so the user re-uploads."""
    from tests.acceptance.chat_harness import image_bytes

    _open(page, app_url)
    _send(page, "what can I say?")
    page.get_by_test_id("help-card").last.get_by_role("button", name=re.compile("A fridge photo")).click()
    expect(page.get_by_label("Message Zest")).to_be_enabled(timeout=15000)
    page.get_by_role("radio", name=re.compile("Meera Shah")).click()
    expect(page.get_by_role("button", name="Apply and rerun “Sample photo RF02”")).to_be_visible()

    photo = tmp_path / "fridge.png"
    photo.write_bytes(image_bytes())
    page.locator("input[type=file]").set_input_files(str(photo))
    expect(page.get_by_label("Message Zest")).to_be_enabled(timeout=15000)
    expect(page.get_by_role("button", name="Apply, then upload your photo again")).to_be_visible()


@pytest.mark.fresh_tour
def test_t126_tour_first_visit_skip_and_restart_from_the_help_icon(page: Page, app_url: str):
    _open(page, app_url)
    tour = page.get_by_test_id("tour")
    expect(tour).to_contain_text("Start here")
    expect(tour).to_contain_text("Step 1 of 6")
    # Step 1 is interactive and the chat is not blocked: a starter moves the tour on
    page.get_by_role("button", name="Feeling hungry").click()
    expect(tour).to_contain_text("Chat with Zest")
    tour.get_by_role("button", name="Back").click()
    expect(tour).to_contain_text("Start here")
    tour.get_by_role("button", name="Skip").click()
    expect(tour).to_be_hidden()
    page.reload()
    expect(page.get_by_text("Hey there! I'm Zest")).to_be_visible()
    expect(page.get_by_test_id("tour")).to_be_hidden()  # dismissal is remembered
    page.get_by_role("button", name="Help and tour").click()  # the top-right help icon restarts it (AC-56)
    expect(tour).to_contain_text("Step 1 of 6")
    titles = ["Chat with Zest", "Who's cooking?", "Levers", "Your cart", "Inspector"]
    for title in titles:
        tour.get_by_role("button", name="Next").click()
        expect(tour).to_contain_text(title)
    expect(tour).to_contain_text("It fills in once you start chatting")
    expect(tour).not_to_contain_text("ⓘ on a suggestion")  # the cart step no longer points at an ⓘ (owner, 2026-10-23)
    page.keyboard.press("Escape")
    expect(tour).to_be_hidden()
