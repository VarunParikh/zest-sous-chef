"""Config defaults and secret handling (architecture §6, ADR-003 v2, NFR-05)."""
from backend.config import Settings, load_settings

FAKE_KEY = "test-value-not-a-real-key"


def test_defaults_match_architecture_section_6():
    s = load_settings(env={}, env_file=None)
    assert s.llm_provider == "ollama"
    assert s.llm_model == "llama3.2:3b"  # ADR-002, accepted 2026-10-18 from E1
    assert s.llm_num_ctx == 4096  # E1 post-hoc change, owner decision 2026-10-18
    assert s.vision_num_ctx == 4096  # set before any official E3 run (smoke showed eviction at 16k)
    assert s.vision_provider == "samples"  # ADR-003 v2 local-first; C15
    assert (s.rrf_k, s.dish_pool, s.variant_pool) == (60, 15, 10)
    assert s.ambiguity_margin == 0.15
    assert s.addon_courses == ["side", "beverage", "dessert"]
    assert s.addon_weights == {"curated": 2.0, "vector": 1.0}
    assert s.addon_pool == 8
    assert s.value_weight == 0.30
    assert (s.timeout_llm_s, s.timeout_vision_s, s.timeout_transcript_s) == (30, 20, 10)
    assert s.confidence_threshold == 0.6
    assert s.demo_controls is False
    assert s.trace_path == "logs/trace.jsonl"


def test_env_overrides_are_parsed():
    s = load_settings(
        env={"LLM_MODEL": "m1", "DEMO_CONTROLS": "true", "RRF_K": "30", "ADDON_COURSES": "side, dessert"},
        env_file=None,
    )
    assert s.llm_model == "m1"
    assert s.demo_controls is True
    assert s.rrf_k == 30
    assert s.addon_courses == ["side", "dessert"]


def test_gemini_disabled_without_key():
    s = load_settings(env={"VISION_PROVIDER": "gemini"}, env_file=None)
    assert s.gemini_enabled is False


def test_gemini_enabled_only_with_key_and_provider():
    s = load_settings(env={"VISION_PROVIDER": "gemini", "GEMINI_API_KEY": FAKE_KEY}, env_file=None)
    assert s.gemini_enabled is True
    s2 = load_settings(env={"GEMINI_API_KEY": FAKE_KEY}, env_file=None)
    assert s2.gemini_enabled is False


def test_key_never_appears_in_repr_or_dump():
    s = load_settings(env={"GEMINI_API_KEY": FAKE_KEY}, env_file=None)
    assert FAKE_KEY not in repr(s)
    assert FAKE_KEY not in str(s)
    assert FAKE_KEY not in s.model_dump_json()


def test_settings_is_a_pydantic_model():
    assert "llm_model" in Settings.model_fields
