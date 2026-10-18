"""E11 latency (Evaluation Plan v0.6 §4.16; C59, C60, C61): server-side time per flow on the target laptop,
in-process with the real models. The owner stops `make app` and closes other apps first; the run is
BLOCKED if free RAM is under 3 GB (the E1 floor).

Flows: mood, text, YouTube (fixture path: live fetch is off, so MSG-YT-FIXTURE is the configured path,
not a fallback), photo upload (local qwen3-vl:4b-instruct, upload plus the confirm taps), sample photo
(the demo path) and cart edit (cart-window API edits, C59). Per flow one unscored warm-up run (the cold
start) and 10 scored runs, each in a fresh session. Model time per call kind comes from `llm_call`.
"""
from __future__ import annotations

import json
import subprocess
import time

from _app import TRACE_DIR, build
from _common import ROOT, parser, rows, save
from text_models import free_ram_gb

from backend.config import load_settings
from backend.evaluation.latency import breakdown, flow_status, summarise
from backend.evaluation.results import environment, make_result

RAM_FLOOR_GB = 3
VIDEOS = [v["url"] for v in json.loads((ROOT / "mock-data/videos.json").read_text())["videos"]]
UPLOADS = ["RF01", "RF02", "RF03", "RF07"]
FALLBACK_TEMPLATES = {"MSG-SERVER", "MSG-REPHRASE", "MSG-PHOTO-SAMPLES", "MSG-YT-PASTE", "MSG-YT-TITLE"}
NORMAL = {"mood": "MSG-MOOD-ADD", "text": "MSG-TXT-DRAFT", "youtube": "MSG-YT-OK", "photo_upload": "MSG-PHOTO-OK",
          "sample_photo": "MSG-PHOTO-OK"}
PREFER = ("yes", "add")


def recipe_text(store, dish_id: str) -> str:  # the E9 generator (scripts/benchmark/intent_to_cart.py)
    rec = store.dish(dish_id)
    parts = [f"{i.qty:g} {i.unit.value} {i.ingredient_name}" for i in rec.ingredients]
    return f"Here is my recipe for {rec.dish.name.replace(' (international)', '')}: " + ", ".join(parts)


def _timed(fn):
    t0 = time.perf_counter()
    r = fn()
    return r, (time.perf_counter() - t0) * 1000


def _templates(r) -> list[str]:
    if r.status_code != 200:
        return [((r.json().get("error") or {}).get("template_id")) or f"HTTP {r.status_code}"]
    return [m["template_id"] for m in r.json().get("messages", [])]


def _next_tap(client, sid, turn):
    """The confirm or clarify tap a user would make next (yes/add, or the first option), or None."""
    for m in turn.get("messages", []):
        for c in m.get("cards", []):
            if c.get("type") == "confirm":
                choice = next((p for p in PREFER if p in [o["value"] for o in c["options"]]), None)
                if choice:
                    return lambda c=c, choice=choice: client.post(
                        f"/api/v1/sessions/{sid}/action", json={"type": "confirm", "payload": {"confirm_id": c["confirm_id"], "choice": choice}})
            if c.get("type") == "clarify" and c["options"]:
                return lambda c=c: client.post(
                    f"/api/v1/sessions/{sid}/action", json={"type": "answer", "payload": {"question_id": c["question_id"], "choice": c["options"][0]["value"]}})
    return None


def chat_run(client, flow: str, payload) -> dict:
    sid = client.post("/api/v1/sessions", json={"levers": {}}).json()["session_id"]
    url = f"/api/v1/sessions/{sid}/chat"
    if flow == "photo_upload":
        data = (ROOT / "assets/sample-photos" / f"{payload}.jpeg").read_bytes()
        call = lambda: client.post(url, data={"text": ""}, files={"image": (f"{payload}.jpeg", data, "image/jpeg")})  # noqa: E731
    elif flow == "sample_photo":
        call = lambda: client.post(url, json={"text": "", "sample_photo_id": payload})  # noqa: E731
    else:
        call = lambda: client.post(url, json={"text": payload})  # noqa: E731
    r, ms = _timed(call)
    steps, templates, fallbacks = [round(ms, 1)], _templates(r), list(r.json().get("fallbacks_used", [])) if r.status_code == 200 else []
    if flow in ("photo_upload", "sample_photo"):  # the confirm taps belong to the flow (FR-55: confirmed before the cart changes)
        turn = r.json() if r.status_code == 200 else {}
        for _ in range(4):
            tap = _next_tap(client, sid, turn)
            if tap is None:
                break
            r, ms = _timed(tap)
            steps.append(round(ms, 1))
            templates += _templates(r)
            if r.status_code != 200:
                break
            turn = r.json()
            fallbacks += turn.get("fallbacks_used", [])
    return {"session_id": sid, "input": payload, "steps_ms": steps, "total_ms": round(sum(steps), 1), "templates": templates,
            "fallbacks_used": fallbacks}


def cart_edit_run(client) -> list[dict]:
    """Setup (untimed): a mood turn carts a dish. Timed: quantity change, line removal, swap, Undo (C59)."""
    sid = client.post("/api/v1/sessions", json={"levers": {}}).json()["session_id"]
    turn = client.post(f"/api/v1/sessions/{sid}/chat", json={"text": "I am feeling indulgent"}).json()
    cards = {c["type"]: c for m in turn.get("messages", []) for c in m.get("cards", [])}
    if "dish_added" not in cards:
        return [{"session_id": sid, "op": "setup", "ms": None, "status": 0, "normal": False, "note": "mood setup did not cart a dish"}]
    owned = [ln for d in turn["cart"]["dishes"] for ln in d["lines"] if ln["priced"] and not ln["shared_from_line_id"]]
    out = []

    def op(name, fn):
        r, ms = _timed(fn)
        out.append({"session_id": sid, "op": name, "ms": round(ms, 1), "status": r.status_code, "normal": r.status_code == 200})
        return r

    op("quantity", lambda: client.patch(f"/api/v1/sessions/{sid}/cart/lines/{owned[0]['line_id']}", json={"quantity": 2}))
    op("remove_line", lambda: client.delete(f"/api/v1/sessions/{sid}/cart/lines/{owned[1]['line_id']}"))
    alt = cards["swap_options"]["options"][0]["dish_id"]
    r = op("swap", lambda: client.post(f"/api/v1/sessions/{sid}/action", json={
        "type": "swap", "payload": {"suggestion_id": cards["dish_added"]["suggestion_id"], "alt_dish_id": alt}}))
    undo = next((c for m in r.json().get("messages", []) for c in m.get("cards", []) if c["type"] == "undo"), None) if r.status_code == 200 else None
    op("undo", lambda: client.post(f"/api/v1/sessions/{sid}/action", json={
        "type": "undo", "payload": {"suggestion_id": (undo or cards["undo"])["suggestion_id"]}}))
    return out


def _llm_by_session(trace_path) -> dict:
    out: dict[str, list] = {}
    for line in trace_path.read_text().splitlines():
        e = json.loads(line)
        if e["event"] == "llm_call":
            out.setdefault(e["session_id"], []).append((e["data"]["call"], e["data"]["latency_ms"], e["data"]["outcome"]))
    return out


def main():
    ap = parser(__doc__)
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--flows", default="mood,text,youtube,sample_photo,cart_edit,photo_upload")
    args = ap.parse_args()
    ram_before = free_ram_gb()
    if ram_before < RAM_FLOOR_GB:
        print(f"BLOCKED: free RAM {ram_before} GB is under the {RAM_FLOOR_GB} GB floor; stop make app and close other apps")
        raise SystemExit(2)
    app, client = build(None, VISION_PROVIDER="ollama")
    store, s = app.state.store, app.state.settings
    texts = [recipe_text(store, r["source"].split(":")[1]) for r in rows("carts_v1.jsonl", "all", False) if r["source"].startswith("text:")]
    moods = {r["id"]: r["text"] for r in rows("levers_v1.jsonl", "all", False)}
    samples = [p["id"] for p in json.loads((ROOT / "mock-data/photos.json").read_text())["photos"] if p["split"] == "demo"]
    inputs = {"mood": ([moods["LD2"]], [moods[f"L{i:02d}"] for i in range(1, 11)]),
              "text": ([recipe_text(store, "D02")], [texts[i % len(texts)] for i in range(args.runs)]),
              "youtube": ([VIDEOS[0]], [VIDEOS[i % len(VIDEOS)] for i in range(args.runs)]),
              "photo_upload": (["RF05"], [UPLOADS[i % len(UPLOADS)] for i in range(args.runs)]),
              "sample_photo": ([samples[-1]], [samples[i % len(samples)] for i in range(args.runs)])}
    per, flows = [], {}
    for flow in args.flows.split(","):
        t_flow = time.time()
        if flow == "cart_edit":
            warm = cart_edit_run(client)
            scored = [x for _ in range(args.runs) for x in cart_edit_run(client)]
            ops = {}
            for x in scored:
                ops.setdefault(x["op"], []).append(x)
            flows[flow] = {"status": flow_status(scored, required=4 * args.runs) if all(x["ms"] is not None for x in scored) else "FAIL",
                           "cold_start_ms": [w["ms"] for w in warm],
                           "per_op": {k: {**summarise([x["ms"] for x in v]), "ok": sum(x["normal"] for x in v)} for k, v in ops.items() if k != "setup"}}
            per += [{"flow": flow, "warm_up": True, **w} for w in warm] + [{"flow": flow, **x} for x in scored]
            print(flow, flows[flow]["status"], flush=True)
            continue
        warm_inputs, run_inputs = inputs[flow]
        warm = [chat_run(client, flow, x) for x in warm_inputs]
        scored = [chat_run(client, flow, x) for x in run_inputs]
        llm = _llm_by_session(app.state.tracer.path)
        for r in warm + scored:
            calls = llm.get(r["session_id"], [])
            r["llm"] = [[c, ms] for c, ms, _ in calls]
            r["llm_outcomes"] = sorted({o for _, _, o in calls})
            r["normal"] = (NORMAL[flow] in r["templates"] and not r["fallbacks_used"]
                           and not set(r["templates"]) & FALLBACK_TEMPLATES and r["llm_outcomes"] in ([], ["ok"]))
        flows[flow] = {"status": flow_status(scored, required=args.runs), "normal_runs": sum(r["normal"] for r in scored),
                       "end_to_end": summarise([r["total_ms"] for r in scored]),
                       "cold_start_ms": [r["total_ms"] for r in warm],
                       "model_breakdown": breakdown([{"total_ms": r["total_ms"], "llm": r["llm"]} for r in scored]),
                       "wall_clock_s": round(time.time() - t_flow, 1)}
        per += [{"flow": flow, "warm_up": True, **r} for r in warm] + [{"flow": flow, "warm_up": False, **r} for r in scored]
        print(flow, flows[flow]["status"], flows[flow]["end_to_end"], flush=True)
    ps = subprocess.run(["ollama", "ps"], capture_output=True, text=True).stdout
    status = "PASS" if all(f["status"] == "PASS" for f in flows.values()) and len(flows) == 6 else "FAIL"
    comparisons = {"E1_extraction_ms": {"median": 4219.0, "p95": 5384.5, "source": "eval/results/post-hoc/E1-llama3.2_3b.json"},
                   "E3_vision_gate_p95_ms": 20000, "timeouts_s": {"llm": s.timeout_llm_s, "vision": s.timeout_vision_s,
                                                                   "transcript": s.timeout_transcript_s}}
    metrics = {"flows": flows, "runs_per_flow": args.runs, "free_ram_gb_before": ram_before, "free_ram_gb_after": free_ram_gb(),
               "comparisons_not_gated": comparisons, "chat_cart_edit": "NOT RUN (FR-78 cut, C59)", "live_youtube": "NOT RUN (network)"}
    save(make_result("E11", "latency-real-stack", "levers_v1.jsonl", "all", metrics, per, [], status,
                     notes="server-side wall clock per API call (browser rendering excluded); p95 by linear interpolation, "
                           "n = 10 so p95 sits near the maximum; inputs: levers_v1 L01-L10, carts_v1 text rows, the 4 fixture "
                           "videos, demo photos; one set of runs; targets are proposed to the owner from these numbers (C60)",
                     env=environment({"ollama_ps": ps, "llm_model": s.llm_model, "llm_num_ctx": s.llm_num_ctx,
                                      "guard_model": s.guard_model, "vision_model": s.vision_model,
                                      "trace_dir": TRACE_DIR})), args.out, args.post_hoc)
    print(status)


if __name__ == "__main__":
    main()
