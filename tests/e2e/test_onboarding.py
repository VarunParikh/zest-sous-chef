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
    meera.click()
    expect(meera).to_have_attribute("aria-checked", "true")
    expect(page.get_by_text("Changes apply from your next chat session.")).to_be_visible()
    page.get_by_role("button", name="Start new chat").click()
    expect(page.get_by_text("Persona: Meera Shah")).to_be_visible()
    # The cards are a radio group: an arrow key moves to and selects the next persona
    meera.press("ArrowRight")
    expect(meera).to_have_attribute("aria-checked", "false")
    expect(page.get_by_role("radio", checked=True)).to_have_count(1)
