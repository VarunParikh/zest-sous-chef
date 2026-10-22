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
