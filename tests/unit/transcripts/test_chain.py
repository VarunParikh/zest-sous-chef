"""Transcript chain and URL rules (FR-20, 22, 24; API Spec §6.3; T-081, T-082 unit level). No network: fakes only."""
import pytest

from backend.transcripts.source import TranscriptChain, TranscriptUnavailable, clean, default_chain, find_url, video_id

RASAM = "6YVx0i_hrZ0"


@pytest.mark.parametrize("text, vid", [
    ("https://www.youtube.com/watch?v=6YVx0i_hrZ0", RASAM),
    ("try this https://youtube.com/watch?v=6YVx0i_hrZ0&t=30s please", RASAM),
    ("https://youtu.be/6YVx0i_hrZ0", RASAM),
    ("https://m.youtube.com/watch?v=6YVx0i_hrZ0", RASAM),
])
def test_youtube_links_give_the_video_id(text, vid):
    assert video_id(text) == vid and find_url(text)


@pytest.mark.parametrize("text", ["https://example.com/recipe/paneer", "https://vimeo.com/123456",
                                  "https://www.youtube.com/@HomeCookingShow", "www.youtube.com.evil.test/watch?v=6YVx0i_hrZ0"])
def test_other_urls_are_not_youtube(text):
    assert video_id(text) is None and find_url(text)


def test_no_url():
    assert find_url("I am feeling indulgent") is None


def _chain(live=None, **kw):
    return default_chain(live=live, **kw)


def test_live_first_then_fixture_then_title_then_unavailable():
    calls = []

    def live_ok(vid, timeout):
        calls.append(vid)
        return "[00:01] Today we make rasam with toor dal. Subscribe to my channel!"

    t = _chain(live=live_ok).fetch(RASAM)
    assert t.source == "live" and "toor dal" in t.text and "00:01" not in t.text and "Subscribe" not in t.text

    def live_down(vid, timeout):
        raise RuntimeError("blocked")

    t = _chain(live=live_down).fetch(RASAM)
    assert t.source == "fixture" and "OWN-WRITTEN" not in t.text and "rasam" in t.text.lower()
    t = _chain(live=live_down, fixtures={}).fetch(RASAM)
    assert t.source == "title" and "Rasam" in t.text
    with pytest.raises(TranscriptUnavailable):
        _chain(live=live_down).fetch("aaaaaaaaaaa")


def test_live_fetch_off_by_config_goes_to_the_fixture():
    assert _chain(live=None).fetch(RASAM).source == "fixture"


def test_live_timeout_falls_through():
    import time

    def slow(vid, timeout):
        time.sleep(timeout + 0.5)
        return "too late"

    chain = TranscriptChain(live=slow, fixtures=_chain().fixtures, titles=_chain().titles, timeout_s=0.2)
    assert chain.fetch(RASAM).source == "fixture"


def test_clean_caps_and_strips():
    text = "1:02 Add salt.\nThis video is sponsored by MockCo. Use code ZEST.\n" + "stir " * 3000
    out = clean(text, 100)
    assert len(out) <= 100 and "sponsored" not in out and "1:02" not in out
