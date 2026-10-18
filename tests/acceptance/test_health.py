"""Health endpoint and page (API Spec §3 endpoint 1, §2, §7; architecture §10; NFR-02)."""
import httpx
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.config import load_settings

COMPONENTS = {"text_model", "vision", "fixtures", "index"}


def _ollama_up(request: httpx.Request) -> httpx.Response:
    assert request.url.path == "/api/tags"
    return httpx.Response(200, json={"models": [{"name": "fake-text:1b"}]})


def _ollama_down(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("connection refused", request=request)


def _client(tmp_path, handler, **env):
    env = {"CHROMA_PATH": str(tmp_path / "chroma"), "TRACE_PATH": str(tmp_path / "trace.jsonl"), **env}
    settings = load_settings(env=env, env_file=None)
    app = create_app(settings, http_transport=httpx.MockTransport(handler))
    return TestClient(app, raise_server_exceptions=False)


def test_health_shape_with_model_served(tmp_path):
    r = _client(tmp_path, _ollama_up, LLM_MODEL="fake-text:1b").get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert set(body["components"]) == COMPONENTS
    tm = body["components"]["text_model"]
    assert tm["status"] == "ok"
    assert tm["served_models"] == ["fake-text:1b"]  # recorded, not assumed
    assert body["components"]["vision"]["provider"] == "ollama"  # ADR-003 v3 default (C37)
    assert body["components"]["vision"]["status"] == "missing"  # the fake Ollama serves no vision model
    assert body["components"]["fixtures"]["status"] == "ok"
    assert body["components"]["index"]["status"] == "not_built"
    assert body["status"] == "degraded"  # index not built yet


def test_model_not_served_is_reported(tmp_path):
    r = _client(tmp_path, _ollama_up, LLM_MODEL="other:7b").get("/api/v1/health")
    assert r.json()["components"]["text_model"]["status"] == "missing"


def test_model_not_configured_is_reported(tmp_path):
    settings = load_settings(env={"CHROMA_PATH": str(tmp_path / "chroma")}, env_file=None).model_copy(update={"llm_model": ""})
    r = TestClient(create_app(settings, http_transport=httpx.MockTransport(_ollama_up))).get("/api/v1/health")
    assert r.json()["components"]["text_model"]["status"] == "not_configured"


def test_ollama_down_degrades_without_failing(tmp_path):
    r = _client(tmp_path, _ollama_down, LLM_MODEL="fake-text:1b").get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "degraded"
    assert body["components"]["text_model"]["status"] == "down"
    assert "Traceback" not in r.text


def test_all_ok_when_index_present(tmp_path):
    (tmp_path / "chroma").mkdir()
    # ADR-003 v3: the default vision provider is a local Ollama model, so it must be served too for "all ok".
    r = _client(tmp_path, _ollama_up, LLM_MODEL="fake-text:1b", VISION_MODEL="fake-text:1b").get("/api/v1/health")
    assert r.json()["status"] == "ok"


def test_gemini_is_never_called_by_health(tmp_path):
    calls = []

    def handler(request):
        calls.append(request.url.host)
        return _ollama_up(request)

    r = _client(tmp_path, handler, VISION_PROVIDER="gemini", GEMINI_API_KEY="test-value-not-a-real-key").get(
        "/api/v1/health"
    )
    vision = r.json()["components"]["vision"]
    assert vision["status"] == "configured_unverified"
    assert all(host in {"127.0.0.1", "localhost"} for host in calls)
    assert "test-value-not-a-real-key" not in r.text


def test_request_id_header(tmp_path):
    r = _client(tmp_path, _ollama_up).get("/api/v1/health")
    assert r.headers.get("X-Request-Id")


def test_health_page_lists_components(tmp_path):
    r = _client(tmp_path, _ollama_up).get("/health")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    for name in ("Text model", "Vision", "Fixtures", "Index"):
        assert name in r.text


def test_cors_allows_localhost_only(tmp_path):
    c = _client(tmp_path, _ollama_up)
    ok = c.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    bad = c.get("/api/v1/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in bad.headers


def test_unhandled_error_hides_stack_trace(tmp_path):
    c = _client(tmp_path, _ollama_up)

    @c.app.get("/api/v1/_boom")
    def boom():
        raise RuntimeError("secret internals")

    r = c.get("/api/v1/_boom")
    assert r.status_code == 500
    assert "secret internals" not in r.text
    assert "Traceback" not in r.text
    assert r.json()["error"]["code"] == "INTERNAL"


def test_fixture_counts_match_files_on_disk(tmp_path):
    from backend.config import REPO_ROOT

    expected = len(list((REPO_ROOT / "mock-data/transcripts").glob("*.txt")))
    fixtures = _client(tmp_path, _ollama_up).get("/api/v1/health").json()["components"]["fixtures"]
    assert fixtures["transcripts"] == expected == 10
    assert fixtures["sample_photos"] == 11
