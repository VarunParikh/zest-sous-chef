"""E10 resilience (Evaluation Plan v0.6 §4.16; C62, C63, C66): the 26 pre-registered scenarios in
`eval/datasets/faults_v1.json`, 3 runs each, in-process with the real local models.

Each run builds a fresh app whose model transport is a `FaultProxy`: unfaulted calls go to the real
Ollama, the target call gets its fault, and no request leaves the machine (Gemini is never
contacted; its scenarios use a placeholder key). F25 and F26 run in a real browser
(`resilience_ui.py`) against a fake model on free ports. The owner's `.env` is never changed:
every override is in-process.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import tempfile
import threading
import time

import httpx
from _app import set_context  # noqa: F401  (puts src/ on the path)
from _common import ROOT, parser, save
from fastapi.testclient import TestClient
from youtube_transcript_api import RequestBlocked

from backend.api.app import create_app
from backend.catalogue.store import load_store
from backend.config import load_settings
from backend.evaluation.resilience import FaultProxy, check_run, scenario_status
from backend.evaluation.results import environment, make_result
from backend.retrieval import vector as vector_module
from backend.transcripts.source import default_chain

DATA = json.loads((ROOT / "eval/datasets/faults_v1.json").read_text())
MOOD = "I am feeling indulgent"
VIDEO = "https://www.youtube.com/watch?v=6YVx0i_hrZ0"
UNKNOWN_VIDEO = "https://www.youtube.com/watch?v=zzzzzzzzzzz"
PHOTO = (ROOT / "assets/sample-photos/RF01.jpeg").read_bytes()
PLACEHOLDER_KEY = "not-a-real-key-e10"


def recipe_text(store, dish_id: str) -> str:  # the E9 generator (scripts/benchmark/intent_to_cart.py)
    rec = store.dish(dish_id)
    parts = [f"{i.qty:g} {i.unit.value} {i.ingredient_name}" for i in rec.ingredients]
    return f"Here is my recipe for {rec.dish.name.replace(' (international)', '')}: " + ", ".join(parts)


class _VectorDown:
    def __getattr__(self, name):
        def fail(*args, **kwargs):
            raise RuntimeError("injected: vector store query failed")
        return fail


def _settings(trace_path: str, overrides: dict):
    env = {"CONTEXT_NOW": "2026-05-16T19:30:00", "CONTEXT_WEATHER": "hot", "LIVE_TRANSCRIPTS": "false",
           "VISION_PROVIDER": "samples", "TRACE_PATH": trace_path, **overrides}
    s = load_settings(env=env)
    if overrides.get("GEMINI_API_KEY"):  # checked without printing: only the placeholder may be set
        assert s.gemini_api_key.get_secret_value() == PLACEHOLDER_KEY
    return s


def _cart(app, sid):
    lines = app.state.sessions.get(sid).cart.lines()
    return sorted((ln.ingredient_name, ln.variant_id, json.dumps([p.model_dump(mode="json") for p in ln.packs], sort_keys=True))
                  for ln in lines)


def _send(client, sid, kind: str, store):
    url = f"/api/v1/sessions/{sid}/chat"
    if kind == "photo_upload":
        return client.post(url, data={"text": "", "consent": "true"}, files={"image": ("RF01.jpeg", PHOTO, "image/jpeg")})
    text = {"mood": MOOD, "video": VIDEO, "unknown_video": UNKNOWN_VIDEO, "text": recipe_text(store, "D21")}[kind]
    return client.post(url, json={"text": text})


def _parse(r) -> dict:
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    if r.status_code == 200:
        msgs = body.get("messages", [])
        return {"templates": [m["template_id"] for m in msgs], "texts": {m["template_id"]: m["text"] for m in msgs},
                "cart_changed": bool(body.get("cart_changed")), "fallbacks_used": body.get("fallbacks_used", []), "error_code": None}
    err = body.get("error", {})
    return {"templates": [err["template_id"]] if err.get("template_id") else [], "texts": {}, "cart_changed": False,
            "fallbacks_used": [], "error_code": err.get("code")}


def run_api_scenario(sc: dict, run: int) -> dict:
    inject, expect = sc["inject"], sc["expect"]
    trace_path = tempfile.mkdtemp(prefix=f"zest-e10-{sc['id']}-") + "/trace.jsonl"
    settings = _settings(trace_path, inject.get("settings", {}))
    base = load_settings()
    proxy = FaultProxy(httpx.HTTPTransport(), inject.get("proxy", {}), guard_model=settings.guard_model)
    app = create_app(settings, llm_transport=proxy)
    app.state.store = load_store()
    client = TestClient(app, raise_server_exceptions=False)

    def blocked(vid, timeout):
        proxy.attempts["transcript_live"] = proxy.attempts.get("transcript_live", 0) + 1
        raise RequestBlocked(vid)

    tr = inject.get("transcripts", {})
    app.state.transcripts = default_chain(live=blocked if tr.get("live") == "blocked" else None,
                                          fixtures={} if tr.get("fixtures") == "none" else None,
                                          timeout_s=settings.timeout_transcript_s, cap=settings.max_recipe_chars)
    original_ensure = vector_module.VectorStore.ensure
    if inject.get("vector") == "build_fails":
        def ensure_fails(self, store):
            raise RuntimeError("injected: vector index unavailable")
        vector_module.VectorStore.ensure = ensure_fails
    elif inject.get("vector") == "query_fails":
        app.state.get_retriever().vector = _VectorDown()
    try:
        sid = client.post("/api/v1/sessions", json={"levers": {}}).json()["session_id"]
        before = _cart(app, sid)
        busy = None
        if "second_message_after_s" in inject:
            box = {}
            first = threading.Thread(target=lambda: box.update(r=_send(client, sid, sc["input"], app.state.store)))
            first.start()
            time.sleep(inject["second_message_after_s"])
            session = app.state.sessions.get(sid)
            state0 = (len(session.messages), _cart(app, sid))
            r2 = client.post(f"/api/v1/sessions/{sid}/chat", json={"text": "and a dessert please"})
            state1 = (len(session.messages), _cart(app, sid))
            first.join(timeout=120)
            busy = {"status": r2.status_code, "code": (r2.json().get("error") or {}).get("code"), "state_unchanged": state0 == state1}
            r = box["r"]
        else:
            r = _send(client, sid, sc["input"], app.state.store)
        parsed = _parse(r)
        after = _cart(app, sid)
        attempts = dict(proxy.attempts)
    finally:
        vector_module.VectorStore.ensure = original_ensure
    events = [json.loads(x) for x in pathlib.Path(trace_path).read_text().splitlines()] if pathlib.Path(trace_path).exists() else []
    trace_fallbacks = [e["data"].get("component") or e["data"].get("dependency") for e in events if e["event"] == "fallback_used"]
    llm_outcomes = [(e["data"].get("call"), e["data"].get("outcome")) for e in events if e["event"] == "llm_call"]
    # Remove the fault (proxy faults and lowered timeouts), then the same session must answer normally.
    proxy.clear()
    app.state.settings = app.state.settings.model_copy(update={"timeout_llm_s": base.timeout_llm_s,
                                                               "timeout_vision_s": base.timeout_vision_s})
    fr = client.post(f"/api/v1/sessions/{sid}/chat", json={"text": MOOD})
    follow = _parse(fr)
    follow_up_ok = fr.status_code == 200 and "MSG-SERVER" not in follow["templates"]
    obs = {"status": r.status_code, **parsed, "cart_before": before, "cart_after": after, "trace_fallbacks": trace_fallbacks,
           "attempts": attempts, "llm_outcomes": llm_outcomes, "follow_up_ok": follow_up_ok, "busy": busy}
    fails = check_run(expect, obs, DATA["success_templates"])
    return {"id": sc["id"], "run": run, "layer": "api", "status_code": r.status_code, "error_code": parsed["error_code"],
            "templates": parsed["templates"], "cart_changed": parsed["cart_changed"], "cart_lines_before": len(before),
            "cart_lines_after": len(after), "fallbacks_used": parsed["fallbacks_used"], "trace_fallbacks": trace_fallbacks,
            "attempts": attempts, "llm_outcomes": [list(x) for x in llm_outcomes], "busy": busy,
            "follow_up": {"status": fr.status_code, "templates": follow["templates"]}, "failures": fails, "pass": not fails}


def main():
    ap = parser(__doc__)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--only", default="", help="comma-separated scenario IDs (plumbing checks only; results go to --out)")
    ap.add_argument("--skip-ui", action="store_true")
    args = ap.parse_args()
    scenarios = [s for s in DATA["scenarios"] if not args.only or s["id"] in args.only.split(",")]
    per = []
    for sc in scenarios:
        if sc["layer"] != "api":
            continue
        for run in range(1, args.runs + 1):
            row = run_api_scenario(sc, run)
            per.append(row)
            print(sc["id"], run, "PASS" if row["pass"] else f"FAIL {row['failures']}", flush=True)
    ui = [s for s in scenarios if s["layer"] == "browser"]
    if ui and not args.skip_ui:
        from resilience_ui import run_browser_scenarios

        for row in run_browser_scenarios(ui, args.runs):
            per.append(row)
            print(row["id"], row["run"], "PASS" if row["pass"] else f"FAIL {row['failures']}", flush=True)
    by_id = {s["id"]: scenario_status([r["failures"] for r in per if r["id"] == s["id"]]) for s in scenarios}
    passed = sum(v == "PASS" for v in by_id.values())
    critical = [{"kind": "crash" if "HTTP 500 (crash)" in f else "false_success", "id": r["id"], "run": r["run"], "detail": f}
                for r in per for f in r["failures"] if f.startswith("HTTP 500") or f.startswith("success template")]
    status = "PASS" if passed == len(scenarios) and len(scenarios) == len(DATA["scenarios"]) else "FAIL"
    if args.only:
        status = "INCONCLUSIVE"  # a partial run never decides E10
    ps = subprocess.run(["ollama", "ps"], capture_output=True, text=True).stdout
    s = load_settings()
    metrics = {"scenarios": len(scenarios), "scenarios_passed": passed, "runs_per_scenario": args.runs,
               "per_scenario": by_id, "runs_failed": sum(not r["pass"] for r in per)}
    save(make_result("E10", "resilience-real-stack", "faults_v1.json", "all", metrics, per, critical, status,
                     notes="real llama3.2:3b, llama-guard3:1b and qwen3-vl:4b-instruct for unfaulted calls; faults injected at "
                           "the transport, transcript chain and vector store; Gemini never contacted (placeholder key); "
                           "F25 and F26 in Chromium with the fake model; 3 runs, a scenario passes only if all runs pass",
                     env=environment({"ollama_ps": ps, "llm_model": s.llm_model, "guard_model": s.guard_model,
                                      "vision_model_local": "qwen3-vl:4b-instruct"})), args.out, args.post_hoc)
    print(status, f"{passed}/{len(scenarios)} scenarios")


if __name__ == "__main__":
    main()
