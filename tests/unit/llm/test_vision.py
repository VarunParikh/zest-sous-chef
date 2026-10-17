"""Photo path: image preparation and vision providers (ADR-003 v2; FR-51, 57; S-03, S-04; T-102)."""
import base64
import io
import json

import httpx
import pytest
from PIL import Image

from backend.llm.image import ImageRejected, prepare_image
from backend.llm.schemas import DetectionResult
from backend.llm.vision import GeminiVision, OllamaVision, SampleVision

FAKE_KEY = "test-value-not-a-real-key-for-gemini"
RESULT = {"items": [{"name": "paneer", "confidence": 0.93}], "scene_is_food": True, "quality": "ok"}


def _jpeg_with_gps(size=(2400, 1600)) -> bytes:
    img = Image.new("RGB", size, (200, 120, 40))
    exif = Image.Exif()
    exif[0x010F] = "PhoneMaker"  # Make
    gps = exif.get_ifd(0x8825)
    gps[1], gps[2], gps[3], gps[4] = "N", (19.0, 4.0, 30.0), "E", (72.0, 52.0, 10.0)
    buf = io.BytesIO()
    img.save(buf, "JPEG", exif=exif.tobytes())
    return buf.getvalue()


def test_t102_exif_and_gps_removed():
    raw = _jpeg_with_gps()
    assert Image.open(io.BytesIO(raw)).getexif().get_ifd(0x8825)  # fixture really carries GPS
    out = prepare_image(raw)
    img = Image.open(io.BytesIO(out))
    assert not img.getexif() and b"Exif" not in out and b"PhoneMaker" not in out


def test_image_downscaled_and_jpeg():
    img = Image.open(io.BytesIO(prepare_image(_jpeg_with_gps())))
    assert img.format == "JPEG" and max(img.size) <= 1280


@pytest.mark.parametrize("payload", [b"not an image at all", b"%PDF-1.4 spoofed", b"\x89PNG\r\n\x1a\nbroken"])
def test_wrong_or_spoofed_type_rejected(payload):
    with pytest.raises(ImageRejected):
        prepare_image(payload)


def test_oversize_rejected():
    with pytest.raises(ImageRejected):
        prepare_image(b"\xff\xd8\xff" + b"0" * (5 * 1024 * 1024 + 1))


def test_ollama_vision_sends_image_and_parses():
    seen = []

    def handler(req):
        body = json.loads(req.content)
        seen.append(body)
        return httpx.Response(200, json={"model": "fake-vl:1b", "message": {"content": json.dumps(RESULT)}})

    v = OllamaVision("http://127.0.0.1:11434", "fake-vl:1b", transport=httpx.MockTransport(handler))
    res = v.detect(prepare_image(_jpeg_with_gps((300, 200))))
    assert isinstance(res, DetectionResult) and res.items[0].name == "paneer"
    msg = seen[0]["messages"][-1]
    assert msg["images"] and base64.b64decode(msg["images"][0])[:2] == b"\xff\xd8"
    assert seen[0]["format"] == "json" and seen[0]["options"]["temperature"] == 0
    assert v.last_served_model == "fake-vl:1b"


def test_gemini_key_in_header_never_in_url_or_errors():
    seen = []

    def handler(req):
        seen.append(req)
        text = json.dumps(RESULT)
        return httpx.Response(200, json={"modelVersion": "gemini-x", "candidates": [{"content": {"parts": [{"text": text}]}}]})

    v = GeminiVision(FAKE_KEY, "gemini-x", transport=httpx.MockTransport(handler))
    res = v.detect(prepare_image(_jpeg_with_gps((300, 200))))
    req = seen[0]
    assert res.quality == "ok" and req.headers["x-goog-api-key"] == FAKE_KEY
    assert FAKE_KEY not in str(req.url) and "key=" not in str(req.url)
    body = json.loads(req.content)
    assert body["contents"][0]["parts"][1]["inline_data"]["mime_type"] == "image/jpeg"
    assert body["generationConfig"]["responseMimeType"] == "application/json"

    def failing(req):
        return httpx.Response(403, json={"error": {"message": f"bad key {FAKE_KEY}"}})

    with pytest.raises(Exception) as exc:
        GeminiVision(FAKE_KEY, "gemini-x", transport=httpx.MockTransport(failing)).detect(prepare_image(_jpeg_with_gps((300, 200))))
    assert FAKE_KEY not in str(exc.value)


def test_sample_vision_is_labelled_and_needs_no_network():
    v = SampleVision()
    res = v.detect_sample("RF03")
    assert res.items and res.scene_is_food and all(0 < i.confidence <= 1 for i in res.items)
    assert v.name == "samples"


def test_gemini_retries_once_on_busy_then_gives_up():
    calls = []

    def flaky(req):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(503, json={"error": {"message": "overloaded"}})
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": json.dumps(RESULT)}]}}]})

    v = GeminiVision(FAKE_KEY, "gemini-x", transport=httpx.MockTransport(flaky), retry_wait_s=0)
    assert v.detect(prepare_image(_jpeg_with_gps((300, 200)))).items and len(calls) == 2
    always = []

    def busy(req):
        always.append(1)
        return httpx.Response(429, json={})

    with pytest.raises(Exception):
        GeminiVision(FAKE_KEY, "gemini-x", transport=httpx.MockTransport(busy), retry_wait_s=0).detect(prepare_image(_jpeg_with_gps((300, 200))))
    assert len(always) == 2  # at most one retry (NFR-10)
