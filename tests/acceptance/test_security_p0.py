"""Security P0 tests T-103 and T-104 (Test Plan §4.10; NFR-06, AC-34; Security Note S-05)."""
import builtins

import pytest

from backend.transcripts.source import default_chain
from tests.acceptance.chat_harness import image_bytes, say, start, upload

CRAFTED = ["file:///etc/passwd", "http://127.0.0.1:11434/api/tags", "http://169.254.169.254/latest/meta-data/",
           "http://10.0.0.5/watch?v=6YVx0i_hrZ0", "https://www.youtube.com.evil.test/watch?v=6YVx0i_hrZ0",
           "https://youtube-com.example/watch?v=6YVx0i_hrZ0"]
SUCCESS = {"MSG-YT-OK", "MSG-YT-FIXTURE", "MSG-YT-TITLE", "MSG-TXT-DRAFT", "MSG-MOOD-ADD"}


@pytest.mark.parametrize("url", CRAFTED)
def test_t104_crafted_urls_are_rejected_with_no_fetch(chat_app, fake, url):
    app, client = chat_app
    fetched = []

    def live(vid, timeout):
        fetched.append(vid)
        raise RuntimeError("must not be called")

    app.state.transcripts = default_chain(live=live)
    sid = start(client)
    r = say(client, sid, url)
    assert r.status_code == 200
    templates = {m["template_id"] for m in r.json()["messages"]}
    assert fetched == [] and not templates & SUCCESS and r.json()["cart"]["item_count"] == 0
    assert not [c for c in fake.calls if c in ("extract", "vision")]  # nothing was read from the URL


def test_t103_image_bytes_are_never_written_to_disk(chat_app, fake, monkeypatch):
    app, client = chat_app
    app.state.settings = app.state.settings.model_copy(update={"vision_provider": "ollama"})
    trace_path = str(app.state.tracer.path)
    writes, real_open = [], builtins.open

    def spying_open(file, mode="r", *args, **kwargs):
        if any(m in mode for m in "wax") and str(file) != trace_path:
            writes.append(str(file))
        return real_open(file, mode, *args, **kwargs)

    sid = start(client)
    monkeypatch.setattr(builtins, "open", spying_open)
    r = upload(client, sid, image_bytes("JPEG", exif_gps=True), content_type="image/jpeg")
    monkeypatch.undo()
    assert r.status_code == 200 and fake.images  # the image reached the (fake) model
    assert writes == []  # only the trace file was written, and T-109 checks it holds no image data
