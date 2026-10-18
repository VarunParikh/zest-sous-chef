"""Photo flow (US-14 to US-16; FR-50 to 57; ADR-003 v3; T-087, T-088, T-089). Fakes only: no real model or Gemini call."""
import io
import json

import httpx
from PIL import Image

from backend.config import load_settings
from tests.acceptance.chat_harness import detection, image_bytes, say, start, trace, upload, find


def _t(r):
    return [m["template_id"] for m in r.json()["messages"]]


def _confirm(client, sid, card, choice):
    return client.post(f"/api/v1/sessions/{sid}/action",
                       json={"type": "confirm", "payload": {"confirm_id": card["confirm_id"], "choice": choice}})


def test_t087_detect_confirm_unsure_items_then_cart_only_the_top_dish_missing_items(chat_app, fake):
    app, client = chat_app
    fake.detection = detection(("paneer", 0.95), ("capsicum", 0.9), ("onion", 0.4))
    sid = start(client)
    r = upload(client, sid, image_bytes())
    assert r.status_code == 200 and _t(r) == ["MSG-PHOTO-LOW"] and fake.calls.count("vision") == 1
    assert r.json()["cart"]["item_count"] == 0  # nothing carted before the confirmation
    msg = r.json()["messages"][0]
    assert msg["text"] == "I'm not sure about onion. Are they in your photo?"
    (card,) = msg["cards"]
    r = _confirm(client, sid, card, "yes")
    out = r.json()
    msg = find(out, "MSG-PHOTO-OK")
    assert out["messages"][-1]["template_id"] == "MSG-ADDON"  # US-19 and msg["text"].startswith("I can see paneer, capsicum, onion.")
    (dish,) = out["cart"]["dishes"]
    carted = {ln["ingredient_name"] for ln in dish["lines"]}
    assert not carted & {"paneer", "capsicum", "onion"}  # only the missing items (FR-54, OQ-9)
    cards = {c["type"]: c for c in msg["cards"]}
    assert len(cards["swap_options"]["options"]) == 2 and all("missing" in o["name"] for o in cards["swap_options"]["options"])
    assert any(c["type"] == "undo" for c in msg["cards"])
    swap = cards["swap_options"]["options"][0]
    swapped = client.post(f"/api/v1/sessions/{sid}/action",
                          json={"type": "swap", "payload": {"suggestion_id": cards["undo"]["suggestion_id"], "alt_dish_id": swap["dish_id"]}}).json()
    (dish,) = swapped["cart"]["dishes"]
    assert not {ln["ingredient_name"] for ln in dish["lines"]} & {"paneer", "capsicum", "onion"}  # swaps keep the exclusions


def test_no_unsure_items_still_needs_one_confirming_tap(chat_app, fake):
    _, client = chat_app
    sid = start(client)
    r = upload(client, sid, image_bytes())
    msg = r.json()["messages"][0]
    assert msg["template_id"] == "MSG-PHOTO-CONFIRM"
    assert msg["text"] == "I think I can see paneer, capsicum (estimates). Shall I find a dish with these?"
    assert r.json()["cart"]["item_count"] == 0
    no = _confirm(client, sid, msg["cards"][0], "no").json()
    assert no["cart"]["item_count"] == 0 and no["cart_changed"] is False


def test_unsure_item_declined_is_left_out(chat_app, fake):
    _, client = chat_app
    fake.detection = detection(("paneer", 0.95), ("capsicum", 0.3))
    sid = start(client)
    card = upload(client, sid, image_bytes()).json()["messages"][0]["cards"][0]
    msg = find(_confirm(client, sid, card, "no").json(), "MSG-PHOTO-OK")
    assert msg["template_id"] == "MSG-PHOTO-OK" and msg["text"].startswith("I can see paneer.")


def test_t088_local_model_failing_or_timing_out_offers_labelled_samples(chat_app, fake):
    app, client = chat_app
    sid = start(client)
    for failure in (httpx.ReadTimeout("slow"), httpx.ConnectError("down")):
        fake.detection = failure
        r = upload(client, sid, image_bytes())
        assert _t(r) == ["MSG-PHOTO-SAMPLES"] and r.json()["fallbacks_used"] == ["vision"]
        (card,) = r.json()["messages"][0]["cards"]
        assert card["type"] == "sample_photos" and card["photos"] and all(p["label"] == "Sample" for p in card["photos"])
    assert any(e["event"] == "fallback_used" and e["data"]["component"] == "vision" for e in trace(app))


def test_t088_samples_provider_offers_samples_without_any_model_call(chat_app, fake):
    app, client = chat_app
    app.state.settings = app.state.settings.model_copy(update={"vision_provider": "samples"})
    sid = start(client)
    r = upload(client, sid, image_bytes())
    assert _t(r) == ["MSG-PHOTO-SAMPLES"] and "vision" not in fake.calls


def test_sample_photo_pick_uses_precomputed_detections(chat_app, fake):
    _, client = chat_app
    sid = start(client)
    r = client.post(f"/api/v1/sessions/{sid}/chat", json={"text": "", "sample_photo_id": "RF03"})
    msg = r.json()["messages"][0]
    assert msg["template_id"] == "MSG-PHOTO-CONFIRM" and "capsicum" in msg["text"]
    assert "vision" not in fake.calls and "gemini" not in fake.calls  # pre-computed; only the guard screens the names
    ok = _confirm(client, sid, msg["cards"][0], "yes").json()
    assert find(ok, "MSG-PHOTO-OK") and ok["cart"]["item_count"] > 0
    blurry = client.post(f"/api/v1/sessions/{sid}/chat", json={"text": "", "sample_photo_id": "RF04"})
    assert _t(blurry) == ["MSG-PHOTO-DARK"]
    assert client.post(f"/api/v1/sessions/{sid}/chat", json={"text": "", "sample_photo_id": "RF99"}).status_code == 400


def test_non_food_photo(chat_app, fake):
    _, client = chat_app
    fake.detection = detection(food=False)
    sid = start(client)
    assert _t(upload(client, sid, image_bytes())) == ["MSG-PHOTO-NONE"]


def test_t089_wrong_type_oversize_spoofed_and_two_images_are_rejected(chat_app, fake):
    _, client = chat_app
    sid = start(client)
    cases = [
        (b"just some text", "text/plain", 415, "UNSUPPORTED_MEDIA"),
        (b"\xff\xd8\xff" + b"0" * (5 * 1024 * 1024), "image/jpeg", 413, "IMAGE_TOO_LARGE"),
        (b"GIF89a" + b"0" * 100, "image/jpeg", 415, "UNSUPPORTED_MEDIA"),  # says JPEG, is not
    ]
    for data, ctype, status, code in cases:
        r = upload(client, sid, data, content_type=ctype)
        assert r.status_code == status, code
        assert r.json()["error"]["code"] == code and r.json()["error"]["template_id"] == "MSG-UPLOAD-REJECT"
    two = [("image", ("a.png", image_bytes(), "image/png")), ("image", ("b.png", image_bytes(), "image/png"))]
    r = upload(client, sid, b"", files=two)
    assert r.status_code == 400 and r.json()["error"]["template_id"] == "MSG-UPLOAD-REJECT"
    assert "vision" not in fake.calls


def test_exif_and_gps_are_stripped_before_the_model_and_no_image_is_traced(chat_app, fake):
    app, client = chat_app
    sid = start(client)
    raw = image_bytes("JPEG", exif_gps=True)
    assert Image.open(io.BytesIO(raw)).getexif()  # the upload carries metadata
    upload(client, sid, raw, content_type="image/jpeg")
    sent = Image.open(io.BytesIO(fake.images[-1]))
    assert not sent.getexif() and "exif" not in sent.info
    log = app.state.tracer.path.read_text()
    assert "/9j/" not in log and "iVBOR" not in log  # no base64 JPEG or PNG in the trace


def test_gemini_opt_in_asks_consent_before_any_upload_leaves(chat_app, fake):
    app, client = chat_app
    app.state.settings = load_settings(env={"VISION_PROVIDER": "gemini", "VISION_MODEL": "gemini-3.5-flash-lite",
                                            "GEMINI_API_KEY": "not-a-real-key-test",
                                            "TRACE_PATH": str(app.state.tracer.path)}, env_file=None)
    sid = start(client)
    r = upload(client, sid, image_bytes())
    msg = r.json()["messages"][0]
    assert msg["template_id"] == "MSG-PHOTO-CONSENT" and msg["cards"][0]["type"] == "photo_consent"
    assert "gemini" not in fake.calls  # nothing sent before consent (FR-50)
    r = upload(client, sid, image_bytes(), consent="true")
    assert _t(r) == ["MSG-PHOTO-CONFIRM"] and fake.calls.count("gemini") == 1
    fake.detection = httpx.ReadTimeout("slow")
    assert _t(upload(client, sid, image_bytes())) == ["MSG-PHOTO-SAMPLES"]  # consent remembered; failure → samples


def test_consent_action_records_consent(chat_app, fake):
    app, client = chat_app
    app.state.settings = load_settings(env={"VISION_PROVIDER": "gemini", "VISION_MODEL": "gemini-3.5-flash-lite",
                                            "GEMINI_API_KEY": "not-a-real-key-test",
                                            "TRACE_PATH": str(app.state.tracer.path)}, env_file=None)
    sid = start(client)
    r = client.post(f"/api/v1/sessions/{sid}/action", json={"type": "consent_photo", "payload": {"choice": "yes"}})
    assert r.status_code == 200
    assert _t(upload(client, sid, image_bytes())) == ["MSG-PHOTO-CONFIRM"]


def test_samples_list_endpoint(chat_app):
    _, client = chat_app
    photos = client.get("/api/v1/samples/photos").json()["photos"]
    assert len(photos) == 11 and all(p["label"] == "Sample" for p in photos)
    assert json.dumps(photos).count("assistant-labelled, unverified") == 11  # FR-55; labels not yet owner-verified
