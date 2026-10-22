"""Zest.app launcher (ADR-011; US-41): T-111 platform check, T-112 model plan, T-113 runtime seeding,
T-114 the packaged server. No real Ollama, network or dialog is used."""
import re
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.config import load_settings
from macapp import launcher as L

ROOT = Path(__file__).resolve().parents[2]
GB = 2**30
MODELS = ["llama3.2:3b", "llama-guard3:1b", "qwen3-vl:4b-instruct"]


# T-111
def test_platform_ok_on_apple_silicon_sonoma_16gb():
    assert L.platform_problems("arm64", "14.0", 16 * GB) == ([], [])


@pytest.mark.parametrize("machine,macos,why", [("x86_64", "15.1", "Apple silicon"), ("arm64", "13.6.1", "macOS 14"),
                                               ("arm64", "", "macOS 14")])
def test_platform_rejects_with_reason(machine, macos, why):
    errors, _ = L.platform_problems(machine, macos, 16 * GB)
    assert len(errors) == 1 and why in errors[0]


def test_platform_warns_below_16gb_but_continues():
    errors, warnings = L.platform_problems("arm64", "27.0.1", 8 * GB)
    assert errors == [] and "8 GB" in warnings[0]


# T-112
def _settings(**env):
    return load_settings(env=env, env_file=None)


def test_required_models_follow_configuration():
    assert L.required_models(_settings()) == MODELS
    assert L.required_models(_settings(GUARD_CLASSIFIER="false", VISION_PROVIDER="samples")) == ["llama3.2:3b"]


def test_reuse_only_when_every_model_is_served():
    assert L.plan_ollama(MODELS + ["other:7b"], MODELS) == "reuse"
    assert L.plan_ollama(MODELS[:2], MODELS) == "private"
    assert L.plan_ollama(None, MODELS) == "private"  # nothing on 11434
    assert L.plan_ollama(MODELS, MODELS, force_private=True) == "private"


def test_missing_models_lists_exactly_the_absent_ones():
    assert L.missing_models(["llama3.2:3b"], MODELS) == MODELS[1:]
    assert L.missing_models(None, MODELS) == MODELS
    assert L.missing_models(["phi:latest"], ["phi"]) == []  # an untagged name means :latest


def test_pull_progress_sums_layers():
    parts: dict = {}
    L.merge_progress(parts, {"status": "pulling manifest"})
    L.merge_progress(parts, {"digest": "a", "total": 300, "completed": 150})
    L.merge_progress(parts, {"digest": "b", "total": 100})
    assert L.percent(parts) == 37.5


def _run_prepare(monkeypatch, tmp_path, fail_times):
    """`fail_times` maps a model to how many of its pulls fail before one succeeds."""
    import threading

    served, attempts = {"models": []}, []

    def pull(base, model, setup):
        attempts.append(model)
        if attempts.count(model) <= fail_times.get(model, 0):
            raise OSError("read: operation timed out")
        served["models"].append(model)
        setup.model(model, status="ready", percent=100.0)  # as the real _pull does

    monkeypatch.setattr(L, "_served", lambda base, timeout=2.0: list(served["models"]))
    monkeypatch.setattr(L, "_pull", pull)
    monkeypatch.setattr(L, "RETRY_BACKOFF_S", 0.0)
    setup = L.Setup(optional=["vision:4b"])
    worker = threading.Thread(target=L.prepare_models, args=("http://x", ["text:3b", "vision:4b"], tmp_path, setup, False),
                              daemon=True)
    worker.start()
    return setup, worker, attempts


def _wait_phase(setup, phases):
    import threading

    for _ in range(300):
        if setup.phase in phases:
            return
        threading.Event().wait(0.01)


def test_dropped_connection_is_retried_without_bothering_the_user(tmp_path, monkeypatch):
    setup, worker, attempts = _run_prepare(monkeypatch, tmp_path, fail_times={"text:3b": L.AUTO_RETRIES - 1})
    worker.join(timeout=5)
    assert setup.phase == "ready" and attempts.count("text:3b") == L.AUTO_RETRIES


def test_repeated_failures_ask_to_retry_and_offer_zest_without_the_photo_model(tmp_path, monkeypatch):
    # text:3b downloads; every automatic attempt for vision:4b fails, the one after Try again succeeds
    setup, worker, attempts = _run_prepare(monkeypatch, tmp_path, fail_times={"vision:4b": L.AUTO_RETRIES})
    _wait_phase(setup, {"error"})
    snap = setup.snapshot()
    assert snap["phase"] == "error" and "Try again" in snap["message"] and "operation timed out" not in snap["message"]
    assert snap["models"]["text:3b"]["status"] == "ready" and snap["models"]["vision:4b"]["status"] == "failed"
    assert snap["can_open"] is True  # only the optional photo model is missing
    setup.retry.set()
    worker.join(timeout=5)
    assert setup.phase == "ready"


def test_cannot_open_while_a_required_model_is_missing():
    assert L.can_open({"text:3b": {"status": "failed"}, "vision:4b": {"status": "ready"}}, ["vision:4b"]) is False
    assert L.can_open({"text:3b": {"status": "ready"}, "vision:4b": {"status": "waiting"}}, ["vision:4b"]) is True
    assert L.can_open({}, []) is False


@pytest.mark.parametrize("status,pct,label", [("pulling f6417cb1e269", 100.0, "Finishing"),
                                              ("pulling 3a859c4dca68", 42.4, "Downloading 42%"),
                                              ("verifying sha256 digest", 100.0, "Verifying"),
                                              ("writing manifest", 100.0, "Finishing"),
                                              ("pulling manifest", 0.0, "Starting")])
def test_stage_label_never_says_downloading_100(status, pct, label):
    assert L.stage_label(status, pct) == label


def test_skip_pull_never_downloads(tmp_path, monkeypatch):
    monkeypatch.setattr(L, "_served", lambda base, timeout=2.0: [])
    monkeypatch.setattr(L, "_pull", lambda *a: pytest.fail("pulled"))
    setup = L.Setup()
    L.prepare_models("http://x", ["m:1b"], tmp_path, setup, skip_pull=True)
    assert setup.phase == "ready" and setup.models["m:1b"]["status"] == "waiting"


# T-113
def test_seed_copies_once_per_version(tmp_path):
    seed = tmp_path / "seed"
    seed.mkdir()
    (seed / "chroma.sqlite3").write_text("v1")
    runtime = tmp_path / "rt"
    assert L.seed_runtime(seed, runtime, "0.1.0+abc") is True
    target = runtime / "data" / "chroma"
    assert (target / "chroma.sqlite3").read_text() == "v1"
    (target / "chroma.sqlite3").write_text("rebuilt by the app")
    assert L.seed_runtime(seed, runtime, "0.1.0+abc") is False  # same version: never overwritten
    assert (target / "chroma.sqlite3").read_text() == "rebuilt by the app"
    assert L.seed_runtime(seed, runtime, "0.1.1+def") is True  # new version: fresh copy
    assert (target / "chroma.sqlite3").read_text() == "v1"


def test_runtime_paths_are_outside_the_bundle(tmp_path):
    env = L.runtime_env(tmp_path, "http://127.0.0.1:11435")
    settings = load_settings(env=env, env_file=None)
    assert settings.resolve(settings.chroma_path) == tmp_path / "data" / "chroma"
    assert settings.resolve(settings.trace_path) == tmp_path / "logs" / "trace.jsonl"
    assert settings.ollama_base_url == "http://127.0.0.1:11435"


def test_user_overrides_skip_blank_values(tmp_path):
    f = tmp_path / "zest.env"
    f.write_text("vision_provider=samples\nGEMINI_API_KEY=\n")
    assert L.user_overrides(f) == {"VISION_PROVIDER": "samples"}
    assert L.user_overrides(tmp_path / "absent.env") == {}


# T-114
@pytest.fixture
def packaged(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><title>Zest frontend</title>")

    def ollama(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"models": [{"name": m} for m in MODELS]})

    env = {"CHROMA_PATH": str(tmp_path / "chroma"), "TRACE_PATH": str(tmp_path / "trace.jsonl")}
    create = lambda: create_app(load_settings(env=env, env_file=None), http_transport=httpx.MockTransport(ollama))  # noqa: E731
    setup = L.Setup()
    return TestClient(L.build_app(setup, dist, create=create)), setup


def test_frontend_served_at_root_and_api_unchanged(packaged):
    client, _ = packaged
    assert "Zest frontend" in client.get("/").text
    health = client.get("/api/v1/health")
    assert health.status_code == 200 and "components" in health.json()
    assert "<html" in client.get("/health").text.lower()  # Zest's own health page, not the static mount
    assert client.get("/api/v1/no-such-route").status_code == 404


def test_every_zest_route_registered_before_the_frontend_mount(packaged):
    from starlette.routing import Mount

    client, _ = packaged
    routes = client.app.routes
    mounts = [i for i, r in enumerate(routes) if isinstance(r, Mount)]
    assert mounts == [len(routes) - 1] and routes[-1].name == "frontend"  # one mount, matched last


def test_setup_status_and_page(packaged):
    client, setup = packaged
    setup.model("llama3.2:3b", status="downloading", percent=42.0)
    setup.set(phase="downloading", message="downloading")
    body = client.get("/launcher/status").json()
    assert body["phase"] == "downloading" and body["models"]["llama3.2:3b"]["percent"] == 42.0
    assert "Getting Zest ready" in client.get("/launcher/").text
    assert client.post("/launcher/retry").json() == {"ok": True} and setup.retry.is_set()


def test_bundle_env_comes_from_the_example_only():
    script = (ROOT / "macapp" / "build_dmg.sh").read_text()
    copies = re.findall(r'cp\s+"?\$ROOT/(\.env[^"\s]*)"?\s+"?\$ZEST/\.env"?', script)
    assert copies == [".env.example"]
