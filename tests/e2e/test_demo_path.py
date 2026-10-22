"""E2E-001 demo path in a real browser (Test Plan §4.9; AC-12, 13, 32; FR-81, 100 to 104). Fake model, real backend."""
import os
import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def test_e2e_001_demo_path(page: Page, app_url: str):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(app_url)

    # Split screen and greeting (FR-100).
    expect(page.get_by_role("heading", name="Recommendation Levers")).to_be_visible()
    expect(page.get_by_role("heading", name="Chat with Zest")).to_be_visible()
    expect(page.get_by_text("Hey there! I'm Zest")).to_be_visible()
    cart = page.locator("button[aria-label='Cart is empty']")
    expect(cart).to_be_disabled()  # FR-75: greyed and disabled when empty

    # Pick a persona preset (Meera Shah has three eligible indulgent dishes); the banner appears (FR-03); start a new session.
    page.get_by_role("radio", name=re.compile("Meera Shah")).click()  # Zest 2.0: persona cards (FR-121)
    expect(page.get_by_text("Changes apply from your next chat session.")).to_be_visible()
    page.get_by_role("button", name="Start new chat").click()
    expect(page.get_by_text("Persona: Meera Shah")).to_be_visible()
    expect(page.get_by_text("Changes apply from your next chat session.")).to_be_hidden()

    # Send the mood message (FR-40, 41).
    page.get_by_label("Message Zest").fill("I am feeling indulgent")
    page.get_by_label("Message Zest").press("Enter")
    expect(page.get_by_text(re.compile("Let's go with"))).to_be_visible(timeout=15000)
    badge = page.locator("button[aria-label^='Open cart']")
    expect(badge).to_be_enabled()

    # The ⓘ icon explains the suggestion (FR-63): reason, biggest factors, score breakdown, runners-up.
    info = page.get_by_role("button", name="Why was this suggested?").first
    info.click()
    expect(info).to_have_attribute("aria-expanded", "true")
    expect(page.get_by_text("Biggest factors:").first).to_be_visible()
    expect(page.get_by_text("Also considered:").first).to_be_visible()
    if os.environ.get("ZEST_SHOTS"):
        page.screenshot(path=os.path.join(os.environ["ZEST_SHOTS"], "why.png"))
    info.click()

    # Tap a swap.
    page.get_by_role("button", name=re.compile("^Swap to")).first.click()
    expect(page.get_by_text(re.compile("^Swapped to"))).to_be_visible(timeout=15000)

    # Tab order reaches the cart icon.
    page.get_by_role("button", name="Clear chat").focus()
    page.keyboard.press("Tab")
    expect(badge).to_be_focused()

    # The cart window traps focus and Escape closes it, returning focus to the icon (FR-103, AC-32).
    badge.click()
    dialog = page.get_by_role("dialog")
    expect(dialog).to_be_visible()
    for _ in range(25):
        page.keyboard.press("Tab")
        assert page.evaluate("document.querySelector('[role=dialog]').contains(document.activeElement)")
    page.keyboard.press("Escape")
    expect(dialog).to_be_hidden()
    expect(badge).to_be_focused()

    # Change a quantity, then Buy Now (FR-74, 80, 81).
    badge.click()
    dialog.get_by_role("button", name="Increase").first.click()
    expect(dialog.get_by_role("group").first.get_by_text("2", exact=True)).to_be_visible()
    dialog.get_by_role("button", name=re.compile("Buy Now")).click()
    expect(dialog.get_by_text("Order is placed, the rider will see you in 10 mins")).to_be_visible()
    expect(dialog.get_by_role("progressbar")).to_be_visible()
    page.keyboard.press("Escape")
    expect(dialog).to_be_visible()  # no Escape during the order state

    # The window collapses after 10 s; the cart is empty and the icon disabled (AC-13, AC-12).
    expect(dialog).to_be_hidden(timeout=13000)
    expect(page.locator("button[aria-label='Cart is empty']")).to_be_disabled()
