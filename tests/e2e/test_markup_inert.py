"""T-075 (S-06; Security Note release blocker 5): markup and script strings in messages render as inert text.
Fake model, real backend, built frontend, as E2E-001."""
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

PAYLOAD = '<b id="zest-bold">bold</b><img src=x onerror="window.__zestXss=1"><script>window.__zestXss=2</script>'


def test_t075_markup_and_scripts_in_messages_render_inert(page: Page, app_url: str):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(app_url)
    expect(page.get_by_text("Hey there! I'm Zest")).to_be_visible()
    page.get_by_label("Message Zest").fill(PAYLOAD)
    page.get_by_label("Message Zest").press("Enter")
    expect(page.get_by_text(PAYLOAD, exact=True)).to_be_visible(timeout=15000)  # shown as literal text
    expect(page.get_by_label("Message Zest")).to_be_enabled(timeout=15000)  # the reply arrived
    assert page.locator("#zest-bold").count() == 0  # no element was created from the text
    assert page.evaluate("window.__zestXss") is None  # no handler or script ran
