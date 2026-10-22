"""T-116 (FR-115, FR-119, US-39): the inspector fills after a named-dish turn, which ranks only the add-on pool,
and explains itself when nothing has been ranked. Fake model, real backend, built frontend, as E2E-001."""
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def _open_inspector(page: Page):
    page.get_by_role("button", name="Retrieval & Scoring Inspector").click()


def test_t116_inspector_shows_the_addon_pool_after_a_named_dish(page: Page, app_url: str):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(app_url)
    expect(page.get_by_text("Hey there! I'm Zest")).to_be_visible()
    _open_inspector(page)
    expect(page.get_by_text("The inspector fills after")).to_be_visible()  # empty state says what fills it
    page.get_by_label("Message Zest").fill("I want to make paneer butter masala")
    page.get_by_label("Message Zest").press("Enter")
    expect(page.get_by_label("Message Zest")).to_be_enabled(timeout=15000)  # the reply arrived
    expect(page.get_by_text("Add-on pool for Paneer Butter Masala")).to_be_visible(timeout=5000)
    expect(page.get_by_text("no dish pool was ranked")).to_be_visible()  # why the dish table is absent
