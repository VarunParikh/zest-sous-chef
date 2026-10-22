"""T-119 (FR-121, AC-50; Zest 2.0): persona-card summaries and tags are generated from each preset's levers."""
import httpx
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.api.sessions import load_presets
from backend.config import load_settings
from backend.session.levers import JAIN_SUMMARY, LeverSet, persona_summary, persona_tag

EXPECTED = {
    "Meera Shah": JAIN_SUMMARY,
    "Rohan Deshmukh": "Pure vegetarian",
    "Imran Qureshi": "Halal only",
    "Ananya Iyer": "Pure vegetarian, Shravan fasting",
    "Karan Malhotra": "Keto, high-protein, eats meat",
    "Priya Nair": "Vegan, gluten-free",
    "Alex (Reviewer)": "No restrictions",
    "Lakshmi Pillai": "Pure vegetarian, low-GI",
    "Jordan Fernandes (control)": "No restrictions",
    "Rahul Verma": "No restrictions",
    "Vikram Rao": "High-protein, eats meat",
}


def test_t119_every_preset_gets_its_summary():
    presets = load_presets()
    assert set(presets) == set(EXPECTED)  # a new preset must be added here, so its card is checked
    assert {n: persona_summary(p) for n, p in presets.items()} == EXPECTED


def test_t119_summary_follows_the_levers_not_the_name():
    jain_by_faith = LeverSet(faith="Jain (Strict Root-Free)")
    assert persona_summary(jain_by_faith) == JAIN_SUMMARY
    assert persona_summary(LeverSet()) == "No restrictions"
    assert "mushrooms" in JAIN_SUMMARY  # Jain excludes fungi (Data Model §9, C68)


def test_t119_tags_mark_reviewer_and_control():
    assert persona_tag("Alex (Reviewer)") == "Reviewer"
    assert persona_tag("Jordan Fernandes (control)") == "Control"
    assert persona_tag("Meera Shah") is None


def test_c81_reviewer_persona_is_never_the_label():
    from backend.session.levers import persona_label

    presets = load_presets()
    assert "Alex (Reviewer)" in presets  # still in personas.json for the evaluations (E9, E13)
    assert persona_label(LeverSet(), presets) == "Jordan Fernandes (control)"


def test_t119_config_endpoint_returns_summary_and_tag(tmp_path):
    env = {"CHROMA_PATH": str(tmp_path / "c"), "TRACE_PATH": str(tmp_path / "t.jsonl")}
    app = create_app(load_settings(env=env, env_file=None), http_transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"models": []})))
    presets = TestClient(app).get("/api/v1/config/levers").json()["presets"]
    offered = {k: v for k, v in EXPECTED.items() if k != "Alex (Reviewer)"}  # C81: the reviewer is not offered
    assert {p["name"]: p["summary"] for p in presets} == offered
    assert {p["name"]: p["tag"] for p in presets if p["tag"]} == {"Jordan Fernandes (control)": "Control"}
