"""Dependency health (API Spec endpoint 1; architecture §10; NFR-02).

Never raises because a dependency is down: each component reports its own status.
Gemini is never called here (no paid or quota-consuming calls from a health check).
"""
from __future__ import annotations

import httpx

from backend.config import Settings

OK = "ok"


async def _ollama_models(settings: Settings, client: httpx.AsyncClient) -> list[str] | None:
    try:
        r = await client.get(f"{settings.ollama_base_url}/api/tags", timeout=2.0)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return None


def _model_status(configured: str, served: list[str] | None) -> str:
    if served is None:
        return "down"
    if not configured:
        return "not_configured"
    return OK if configured in served else "missing"


def _text_model(settings: Settings, served: list[str] | None) -> dict:
    return {
        "status": _model_status(settings.llm_model, served),
        "provider": settings.llm_provider,
        "configured_model": settings.llm_model,
        "served_models": served or [],
    }


def _vision(settings: Settings, served: list[str] | None) -> dict:
    out = {"provider": settings.vision_provider, "configured_model": settings.vision_model}
    if settings.vision_provider == "ollama":
        out["status"] = _model_status(settings.vision_model, served)
    elif settings.vision_provider == "gemini":
        out["status"] = "configured_unverified" if settings.gemini_enabled else "not_configured"
    else:
        out["status"] = OK if settings.resolve("mock-data/photos.json").exists() else "missing"
    return out


def _fixtures(settings: Settings) -> dict:
    folder = settings.resolve("mock-data/transcripts")
    photos = settings.resolve("assets/sample-photos")
    transcripts = len(list(folder.glob("*.txt"))) if (folder / "index.json").exists() else 0
    sample_photos = len([p for p in photos.glob("*") if p.is_file()]) if photos.exists() else 0
    present = transcripts > 0 and sample_photos > 0 and settings.resolve("mock-data/photos.json").exists()
    return {"status": OK if present else "missing", "transcripts": transcripts, "sample_photos": sample_photos}


def _index(settings: Settings) -> dict:
    return {"status": OK if settings.resolve(settings.chroma_path).is_dir() else "not_built"}


async def check_health(settings: Settings, client: httpx.AsyncClient) -> dict:
    served = await _ollama_models(settings, client)
    components = {
        "text_model": _text_model(settings, served),
        "vision": _vision(settings, served),
        "fixtures": _fixtures(settings),
        "index": _index(settings),
    }
    overall = OK if all(c["status"] == OK for c in components.values()) else "degraded"
    return {"status": overall, "components": components}


LABELS = {"text_model": "Text model", "vision": "Vision", "fixtures": "Fixtures", "index": "Index"}


def render_page(report: dict) -> str:
    """A plain HTML health page (no template dependency). Values are escaped."""
    from html import escape

    rows = []
    for key, comp in report["components"].items():
        details = ", ".join(f"{escape(k)}: {escape(str(v))}" for k, v in comp.items() if k != "status")
        status = escape(comp["status"])
        rows.append(f"<tr><th>{LABELS[key]}</th><td class='{status}'>{status}</td><td>{details}</td></tr>")
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'><title>Zest health</title>"
        "<style>body{font-family:system-ui,sans-serif;margin:2rem;background:#fff;color:#111}"
        "table{border-collapse:collapse}th,td{border:1px solid #ccc;padding:.4rem .8rem;text-align:left}"
        ".ok{color:#0a6b2d;font-weight:600}td:not(.ok):nth-child(2){color:#9a3b00;font-weight:600}</style>"
        f"</head><body><h1>Zest health: {escape(report['status'])}</h1>"
        "<p>All commerce data in Zest is mock data.</p>"
        f"<table><tr><th>Component</th><th>Status</th><th>Details</th></tr>{''.join(rows)}</table>"
        "</body></html>"
    )
