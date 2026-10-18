"""Evidence report (Evaluation Plan §9; v0.7 §4.17, C69 to C71).

Inputs: every result file under `eval/results/`, `eval/headline.yaml` (C64), `eval/thresholds.yaml` and git
metadata passed in by the caller (repository HEAD and, per file, the code commits since its own commit).
No number is typed here: every value shown is read from a result or the thresholds file, and a missing
result renders as NOT RUN. Output is deterministic (no build time), so a rebuild of unchanged inputs gives
identical bytes. The overall status follows §7 as written (C70).
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

REQUIRED = [f"E{i}" for i in range(1, 15)]
QUESTIONS = {
    "E1": "Text model: extraction quality and latency", "E2": "Intent classification", "E3": "Vision (photo detection)",
    "E4": "Input guard", "E5": "Retrieval and add-ons", "E6": "Lever sensitivity", "E7": "Persona constraint compliance",
    "E8": "Price and data integrity", "E9": "Intent-to-cart accuracy", "E10": "Resilience (fault injection)",
    "E11": "Latency", "E12": "Variant scoring", "E13": "Reason-line quality", "E14": "Traceability",
}
# Comparison arms behind each ADR decision (file patterns, never numbers).
DECISIONS = [
    ("ADR-002 text model", "E1", ["E1-*.json", "post-hoc/E1-*.json"]),
    ("ADR-003 vision", "E3", ["E3-*.json"]),
    ("ADR-004 and ADR-005 retrieval", "E5", ["post-hoc/c68/E5-*.json", "E5-*nomic*.json"]),
    ("ADR-004 add-ons", "E5_addons", ["post-hoc/c68/E5_addons-*.json"]),
    ("ADR-006 guard", "E4", ["post-hoc/c55/E4-*guard_v3.json"]),
    ("ADR-008 variant scoring", "E12", []),
]
FLOW_TARGET = {"mood": "mood", "text": "text", "youtube": "youtube_fixture", "photo_upload": "photo_upload_local",
               "sample_photo": "sample_photo", "cart_edit": "cart_edit"}


# -- loading ------------------------------------------------------------------------------------------
def load_inputs(results_dir: Path, headline: dict, thresholds: dict) -> dict:
    results_dir = Path(results_dir)
    all_results = {str(p.relative_to(results_dir)): json.loads(p.read_text()) for p in sorted(results_dir.rglob("*.json"))}
    heads = {}
    for eid, h in headline.items():
        heads[eid] = {"files": {f: all_results.get(f) for f in h.get("files", [])}, "accepted": h.get("accepted"),
                      "not_run_by_owner": h.get("not_run_by_owner") or {}}
    e14 = sorted((r["environment"].get("date", ""), f) for f, r in all_results.items() if r.get("id") == "E14")
    if e14 and "E14" not in heads:  # E14 cannot be in headline.yaml (C64); its newest run is its headline
        heads["E14"] = {"files": {e14[-1][1]: all_results[e14[-1][1]]}, "accepted": None, "not_run_by_owner": {}}
    return {"results": all_results, "headline": heads, "thresholds": thresholds, "results_dir": results_dir}


def _resolved(conflicts_md: str, cid: str | None) -> bool:
    if not cid:
        return False
    row = next((ln for ln in conflicts_md.splitlines() if ln.startswith(f"| {cid} |")), "")
    return bool(row) and "Resolved" in row.rsplit("|", 2)[-2]


def _arms(inputs: dict, patterns: list[str]) -> list[tuple[str, dict]]:
    root, out = inputs["results_dir"], []
    for pat in patterns:
        for p in sorted(root.glob(pat)):
            rel = str(p.relative_to(root))
            if rel in inputs["results"] and rel not in [a for a, _ in out]:
                out.append((rel, inputs["results"][rel]))
    return out


# -- model --------------------------------------------------------------------------------------------
def build_model(inputs: dict, conflicts_md: str, git: dict) -> dict:
    heads = inputs["headline"]
    missing, critical, open_fails, accepted, not_run = [], [], [], [], []
    for eid in REQUIRED:
        h = heads.get(eid)
        if not h or not h["files"] or any(r is None or r.get("status") == "NOT RUN" for r in h["files"].values()):
            missing.append(eid)
            continue
        for f, r in h["files"].items():
            for c in r.get("critical_failures") or []:
                critical.append({"eval": eid, "file": f, "detail": c})
            if r["status"] != "PASS":
                if _resolved(conflicts_md, h["accepted"]):
                    accepted.append({"eval": eid, "file": f, "conflict": h["accepted"]})
                else:
                    open_fails.append({"eval": eid, "file": f})
        for f, why in h["not_run_by_owner"].items():
            not_run.append({"eval": eid, "file": f, "reason": why})
    overall = "FAIL" if critical or open_fails or accepted else ("INCONCLUSIVE" if missing else "PASS")
    used = {f: r for h in heads.values() for f, r in h["files"].items() if r is not None}
    decisions = []
    for title, eid, pats in DECISIONS:
        arms = _arms(inputs, pats)
        decisions.append({"title": title, "eval": eid, "arms": arms})
        used.update(dict(arms))
    post_hoc = [(f, r["notes"] if str(r.get("notes", "")).startswith("POST-HOC")
                 else "rerun filed under post-hoc/; its script did not record its reason (fixed in block 3.2)")
                for f, r in sorted(used.items()) if str(r.get("notes", "")).startswith("POST-HOC") or f.startswith("post-hoc/")]
    return {"summary": {"overall": overall, "missing": missing, "critical": critical, "open_fails": open_fails,
                        "accepted": accepted, "not_run_by_owner": not_run},
            "headline": heads, "decisions": decisions, "used": dict(sorted(used.items())), "post_hoc": post_hoc,
            "thresholds": inputs["thresholds"], "git": git}


# -- formatting -----------------------------------------------------------------------------------------
def _r(x, d=2):
    return "NOT RUN" if x is None else f"{x:.{d}f}"


def kn(p) -> str:
    if not isinstance(p, dict) or not p.get("n"):
        return "NOT RUN"
    lo, hi = p["ci95"]
    return f"{p['k']}/{p['n']} ({p['rate']:.2f}; 95% CI {lo:.2f}–{hi:.2f})"


def secs(ms) -> str:
    return "NOT RUN" if ms is None else f"{ms / 1000:.2f} s"


def _agg(m: dict, key: str) -> str:
    a = (m.get("aggregate") or {}).get(key)
    if not a:
        return "NOT RUN"
    bound = f"≥ {a['min']}" if "min" in a else f"≤ {a.get('max')}"
    return f"{a['median']:.2f} (gate {bound}; runs {', '.join(f'{x:.2f}' for x in a['runs'])})"


def _first(h: dict) -> tuple[str, dict]:
    return next(iter(h["files"].items())) if h and h["files"] else ("", {})


def _m(model: dict, eid: str, idx: int = 0) -> tuple[str, dict]:
    h = model["headline"].get(eid)
    items = list(h["files"].items()) if h else []
    if len(items) <= idx or items[idx][1] is None:
        return "", {}
    return items[idx][0], items[idx][1]


def _status(model, eid) -> str:
    h = model["headline"].get(eid)
    if eid in model["summary"]["missing"]:
        return "NOT RUN"
    st = {r["status"] for r in h["files"].values()}
    s = "FAIL" if st - {"PASS"} else "PASS"
    if s == "FAIL" and any(a["eval"] == eid for a in model["summary"]["accepted"]):
        s += f" (accepted, {h['accepted']})"
    return s


# -- sections (shared by both renderers: lists of blocks) -----------------------------------------------
def sections(model: dict) -> list[tuple[str, list]]:
    """Each section is a title and a list of blocks: ("p", text), ("table", header, rows), ("chart", kind, data)."""
    th, out = model["thresholds"], []
    # 1 status and environment
    rows = []
    for eid in REQUIRED:
        h = model["headline"].get(eid) or {"files": {}}
        for f, r in (h["files"].items() or [("", None)]):
            env = (r or {}).get("environment", {})
            rows.append([eid, QUESTIONS[eid], _status(model, eid), f or "NOT RUN", env.get("commit", ""), env.get("date", "")[:10]])
    out.append(("1. Evaluation status and environment", [
        ("p", f"Repository HEAD `{model['git'].get('head', '')}`. Hardware and library versions are recorded in each result file."),
        ("table", ["Eval", "Question", "Status", "Headline result file", "Commit", "Date"], rows)]))
    # 2 decisions
    blocks = []
    for d in model["decisions"]:
        if d["eval"] == "E12":
            _, r = _m(model, "E12")
            g = (r.get("metrics") or {}).get("gates_by_beta0", {})
            rows = [[b, f"{v['organic']['k']}/{v['organic']['n']}", f"{v['gourmet']['k']}/{v['gourmet']['n']}",
                     f"{v['price']['k']}/{v['price']['n']}", str(v.get("price_overrides_organic")), v.get("status", "")]
                    for b, v in sorted(g.items())]
            blocks += [("p", f"**{d['title']}** (E12). Shipped β0: {(r.get('metrics') or {}).get('shipped_beta0', 'NOT RUN')}."),
                       ("table", ["β0", "Organic visible", "Gourmet visible", "Price visible", "Price overrides organic", "Status"], rows or [["NOT RUN"] * 6])]
            continue
        rows = []
        for f, r in d["arms"]:
            m = r.get("metrics", {})
            if d["eval"] == "E1":
                vals = [f"F1 {_r(m.get('extraction_f1_mean'))}", f"schema {kn(m.get('schema_valid'))}",
                        f"p95 {secs(m.get('latency_ms_p95'))}; free RAM after {m.get('free_ram_gb_after', 'NOT RUN')} GB"]
            elif d["eval"] == "E3":
                vals = [f"precision {kn(m.get('precision_clear'))}", f"recall {kn(m.get('recall_clear'))}", f"p95 {secs(m.get('latency_ms_p95'))}"]
            elif d["eval"] == "E5":
                o, mood = m.get("overall", {}), m.get("mood", {})
                vals = [f"recall@pool {kn(o.get('recall_at_pool'))}", f"mood {kn(mood.get('recall_at_pool'))}", f"MRR {_r(o.get('mrr'))}"]
            elif d["eval"] == "E5_addons":
                vals = [f"curated pairs in top 5 {kn(m.get('curated_pair_recovery_top5'))}", f"no-pair coverage {kn(m.get('no_pair_dish_coverage'))}", ""]
            else:  # E4
                vals = [f"attacks blocked {_agg(m, 'attack_block_rate')}", f"false positives {_agg(m, 'false_positive_rate')}", ""]
            rows.append([r.get("system", f), *vals, r.get("status", ""), f])
        blocks += [("p", f"**{d['title']}** ({d['eval']})."),
                   ("table", ["System", "Measure 1", "Measure 2", "Measure 3", "Status", "File"], rows or [["NOT RUN"] + [""] * 5])]
    out.append(("2. Decisions and the evidence behind them", blocks))
    # 3 lever sensitivity
    f6, r6 = _m(model, "E6")
    m6 = r6.get("metrics", {})
    gate = (th.get("E6_lever_sensitivity") or {}).get("rdi_min")
    groups = m6.get("groups", {})
    na = lambda x: "n/a" if x is None else f"{x:.2f}"  # noqa: E731  (an under-exercised group ran but has no RDI)
    rows = [[g, na(v.get("rdi")), str(v.get("applicable", "")), na(v.get("random_rdi_expected")), v.get("status", "")] for g, v in groups.items()]
    blocks = [("p", f"RDI = mean share of the top 3 that changes when one lever group moves (gate ≥ {gate}). Source `{f6 or 'NOT RUN'}`."),
              ("chart", "rdi", {"groups": groups, "gate": gate}),
              ("table", ["Lever group", "RDI", "Applicable prompts", "Random re-ranker RDI", "Status"], rows or [["NOT RUN"] + [""] * 4]),
              ("p", f"Under-exercised (INCONCLUSIVE): {', '.join(m6.get('under_exercised', [])) or 'none'}.")]
    if m6.get("persona_overlap_top3"):
        blocks.append(("chart", "overlap", {"personas": m6.get("personas", []), "pairs": m6["persona_overlap_top3"]}))
        blocks.append(("table", ["Persona pair", "Top-3 overlap"], [[k, _r(v)] for k, v in m6["persona_overlap_top3"].items()]))
    out.append(("3. Lever sensitivity (E6)", blocks))
    # 4 retrieval
    f5, r5 = _m(model, "E5")
    m5 = r5.get("metrics", {})
    rows = [[k, kn(v.get("recall_at_pool")), kn(v.get("recall_at_5")), _r(v.get("mrr"))] for k, v in m5.items() if isinstance(v, dict)]
    retr = next((d for d in model["decisions"] if d["eval"] == "E5"), {"arms": []})
    out.append(("4. Retrieval (E5)", [
        ("p", f"Shipped system: hybrid BM25 plus Chroma, RRF k 60. Source `{f5 or 'NOT RUN'}`."),
        ("table", ["Query type", "Recall@pool", "Recall@5", "MRR"], rows or [["NOT RUN", "", "", ""]]),
        ("chart", "recall", {"arms": [(r.get("system", f), (r.get("metrics", {}).get("overall") or {}).get("recall_at_pool")) for f, r in retr["arms"]]})]))
    # 5 safety and quality
    rows = []
    for i, label in ((0, "adversarial"), (1, "real model")):
        f, r = _m(model, "E7", i)
        m = r.get("metrics", {})
        rows.append([f"E7 {label}", f"{m.get('violations', 'NOT RUN')} violations in {m.get('surfaces_checked', 'NOT RUN')} checks ({m.get('prompts', '')} prompts)", r.get("status", "NOT RUN"), f])
    f, r = _m(model, "E4"); rows.append(["E4 guard (held-out guard_v3)", f"attacks blocked {_agg(r.get('metrics', {}), 'attack_block_rate')}; false positives {_agg(r.get('metrics', {}), 'false_positive_rate')}", _status(model, "E4"), f])
    f, r = _m(model, "E2"); rows.append(["E2 intent", f"accuracy {_agg(r.get('metrics', {}), 'accuracy')}; false unsafe {_agg(r.get('metrics', {}), 'false_unsafe_rate')}", _status(model, "E2"), f])
    f, r = _m(model, "E9"); m = r.get("metrics", {})
    rows.append(["E9 intent to cart", f"precision {_agg(m, 'precision')}; recall {_agg(m, 'recall')}; injection attacks checked {m.get('injections_checked', 'NOT RUN')}, critical {len(r.get('critical_failures') or [])}", _status(model, "E9"), f])
    f, r = _m(model, "E8"); m = r.get("metrics", {})
    rows.append(["E8 integrity", f"{m.get('mismatches', 'NOT RUN')} mismatches in {m.get('carts', 'NOT RUN')} carts", _status(model, "E8"), f])
    f, r = _m(model, "E13"); rows.append(["E13 reason lines", f"validator pass {_agg(r.get('metrics', {}), 'validator_pass_rate')}", _status(model, "E13"), f])
    f, r = _m(model, "E14"); m = r.get("metrics", {})
    rows.append(["E14 traceability", f"Must stories {m.get('must_stories_with_passing_test', 'NOT RUN')}/{m.get('must_stories', '')}; ACs {m.get('acs_mapped_and_passing', 'NOT RUN')}/{m.get('acs', '')}", _status(model, "E14"), f])
    f10, r10 = _m(model, "E10"); m10 = r10.get("metrics", {})
    out.append(("5. Safety, integrity and quality", [
        ("table", ["Check", "Result", "Status", "File"], rows),
        ("p", f"E10 resilience: {m10.get('scenarios_passed', 'NOT RUN')} of {m10.get('scenarios', 'NOT RUN')} pre-registered fault scenarios pass, each in all {m10.get('runs_per_scenario', '')} runs (`{f10 or 'NOT RUN'}`)."),
        ("chart", "matrix", {"per_scenario": m10.get("per_scenario", {})}),
        ("p", "O8 (responsible AI) is evidenced by documents (consent notice, data handling, mock-data labels), not measured by an evaluation: see `docs/epics/zest/design/security-privacy-note.md`.")]))
    # 6 latency
    f11, r11 = _m(model, "E11"); m11 = r11.get("metrics", {})
    targets = ((th.get("targets") or {}).get("NFR01_p95_s")) or {}
    rows, chart = [], []
    for flow, v in (m11.get("flows") or {}).items():
        t = targets.get(FLOW_TARGET.get(flow, flow))
        if "end_to_end" in v:
            e = v["end_to_end"]
            rows.append([flow, secs(e.get("median_ms")), secs(e.get("p95_ms")), "NOT SET" if t is None else f"{t:g} s", str(v.get("normal_runs", e.get("n"))), v.get("status", "")])
            chart.append((flow, e.get("median_ms"), e.get("p95_ms"), None if t is None else t * 1000))
        else:
            ops = v.get("per_op", {})
            rows.append([flow, "; ".join(f"{k} {o['median_ms']:g} ms" for k, o in ops.items()), "; ".join(f"{k} {o['p95_ms']:g} ms" for k, o in ops.items()),
                         "NOT SET" if t is None else f"{t * 1000:g} ms", "", v.get("status", "")])
    comp = m11.get("comparisons_not_gated", {})
    out.append(("6. Latency (E11)", [
        ("p", f"Server-side time per API call on the target laptop; 10 runs per flow after a warm-up; p95 by linear interpolation. Source `{f11 or 'NOT RUN'}`."),
        ("table", ["Flow", "Median", "p95", "NFR-01 target p95", "Normal runs", "Status"], rows or [["NOT RUN"] + [""] * 5]),
        ("chart", "latency", {"flows": chart}),
        ("p", f"Compared, not gated: E1 extraction median {secs((comp.get('E1_extraction_ms') or {}).get('median'))}, p95 {secs((comp.get('E1_extraction_ms') or {}).get('p95'))}; E3 vision gate p95 {secs(comp.get('E3_vision_gate_p95_ms'))}. Free RAM before the run: {m11.get('free_ram_gb_before', 'NOT RUN')} GB.")]))
    # 7 limitations
    s = model["summary"]
    items = ["Datasets are small (n = 5 to 220), so most 95% intervals are wide; a point-estimate pass is reported with its interval (C28).",
             "Prompts and fixtures are English only; code-mixed and regional-language robustness is untested.",
             "Dataset and photo labels were written by the assistant; the owner reviewed a sample only. The C67 spot checks (reason lines, SKU audit) were done by the assistant at the owner's direction and are not independent.",
             "Mock data only: prices, stock, brands and nutrition are invented.",
             'Reason lines may echo catalogue tags such as "high protein" (owner decision C68, 1A).']
    items += [f"Accepted FAIL: {a['eval']} (`{a['file']}`, {a['conflict']})." for a in s["accepted"]]
    items += [f"Not run by owner decision: {n['eval']} `{n['file']}` ({n['reason']})." for n in s["not_run_by_owner"]]
    items += [f"Post-hoc: `{f}`: {re.sub(r';?\s*first results? kept.*$', '', re.sub(r'^POST-HOC rerun:\s*', '', n))[:240]}" for f, n in model["post_hoc"]]
    out.append(("7. Known limitations", [("list", items)]))
    # 8 reproduce
    stale = model["git"].get("staleness", {})
    prov = [[f, r.get("id", ""), r.get("status", ""), r.get("environment", {}).get("commit", ""),
             r.get("environment", {}).get("date", "")[:19], str(stale.get(f, ""))] for f, r in model["used"].items()]
    out.append(("8. Reproduce, provenance and staleness", [
        ("code", "make test && make test-e2e && make test-embedder\nmake eval      # every headline harness; long; close other apps for E11\nmake report    # this page"),
        ("p", "Every number on this page is read from the files below. Staleness = commits to `src/`, `mock-data/` or `eval/datasets/` after the file's own commit (reported, not gated)."),
        ("table", ["File", "Eval", "Status", "Commit", "Date (UTC)", "Code commits since"], prov)]))
    return out


def _header_lines(model: dict) -> list[str]:
    s = model["summary"]
    lines = [f"Overall status: {s['overall']} (Evaluation Plan §7 applied as written, C70)."]
    lines.append("Critical failures: " + ("; ".join(f"{c['eval']} `{c['file']}`: {json.dumps(c['detail'])[:160]}" for c in s["critical"]) or "none") + ".")
    lines.append("Open FAILs: " + ", ".join(f"{o['eval']} `{o['file']}`" for o in s["open_fails"]) + "." if s["open_fails"] else "No open FAIL.")
    lines.append("FAILs accepted by the owner as known limitations: " + (", ".join(f"{a['eval']} ({a['conflict']})" for a in s["accepted"]) or "none") + ".")
    lines.append("Required evaluations without a result: " + (", ".join(s["missing"]) or "none") + " (C69).")
    if s["not_run_by_owner"]:
        lines.append("Not run by owner decision (listed, not counted): " + ", ".join(f"{n['eval']} `{n['file']}`" for n in s["not_run_by_owner"]) + ".")
    return lines


# -- Markdown -------------------------------------------------------------------------------------------
def render_markdown(model: dict) -> str:
    out = ["# Zest evidence report", "", "Generated by `make report` from `eval/results/`, `eval/headline.yaml` and `eval/thresholds.yaml` "
           "(Evaluation Plan §9, v0.7 §4.17). No number on this page is typed by hand.", ""]
    out += [f"- {ln}" for ln in _header_lines(model)] + [""]
    for title, blocks in sections(model):
        out += [f"## {title}", ""]
        for b in blocks:
            if b[0] == "p":
                out += [b[1], ""]
            elif b[0] == "list":
                out += [f"- {x}" for x in b[1]] + [""]
            elif b[0] == "code":
                out += ["```", b[1], "```", ""]
            elif b[0] == "table":
                out += ["| " + " | ".join(b[1]) + " |", "|" + "---|" * len(b[1])]
                out += ["| " + " | ".join(str(c).replace("|", "\\|") for c in row) + " |" for row in b[2]] + [""]
    return "\n".join(out).rstrip() + "\n"


# -- HTML ---------------------------------------------------------------------------------------------
CSS = """
:root{color-scheme:light;--surface:#fcfcfb;--panel:#ffffff;--text:#0b0b0b;--text-2:#52514e;--muted:#8a897f;--rule:#e4e3dd;
--series:#2a78d6;--good:#0ca30c;--critical:#d03b3b;--gate:#52514e;--seq-0:#cde2fb;--seq-1:#104281}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--surface:#1a1a19;--panel:#222220;--text:#f0efec;
--text-2:#c3c2b7;--muted:#8f8e86;--rule:#3a3a37;--series:#3987e5;--gate:#c3c2b7;--seq-0:#1d2a3a;--seq-1:#86b6ef}}
:root[data-theme="dark"]{color-scheme:dark;--surface:#1a1a19;--panel:#222220;--text:#f0efec;--text-2:#c3c2b7;--muted:#8f8e86;
--rule:#3a3a37;--series:#3987e5;--gate:#c3c2b7;--seq-0:#1d2a3a;--seq-1:#86b6ef}
body{margin:0;background:var(--surface);color:var(--text);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1080px;margin:0 auto;padding:24px 16px 64px}h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:36px 0 10px;
border-top:1px solid var(--rule);padding-top:20px}p,li{color:var(--text-2)}code{font-size:13px}
.status{border:1px solid var(--rule);border-radius:10px;background:var(--panel);padding:14px 16px;margin:16px 0}
.status li{color:var(--text)}.chip{display:inline-block;font-weight:600;padding:1px 8px;border-radius:6px;border:1px solid currentColor}
.chip.PASS{color:var(--good)}.chip.FAIL,.chip.INCONCLUSIVE{color:var(--critical)}
.tbl{overflow-x:auto;margin:8px 0 16px}table{border-collapse:collapse;font-size:13px;min-width:100%}
th,td{border-bottom:1px solid var(--rule);padding:6px 8px;text-align:left;vertical-align:top}th{color:var(--text-2);font-weight:600}
td{color:var(--text)}pre{background:var(--panel);border:1px solid var(--rule);border-radius:8px;padding:12px;overflow-x:auto}
svg{max-width:100%;height:auto;display:block;margin:8px 0}svg text{fill:var(--text-2);font-size:11px}
svg .bar{fill:var(--series)}svg .gate{stroke:var(--gate);stroke-dasharray:4 3}svg .tick{stroke:var(--text)}svg .grid{stroke:var(--rule)}
svg .ok{fill:var(--good)}svg .bad{fill:var(--critical)}svg .lbl{fill:var(--text)}
"""


def _e(x) -> str:
    return html.escape(str(x), quote=True)


def _md_inline(text: str) -> str:
    t = _e(text)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)


def _hbars(rows: list[tuple[str, float | None]], vmax: float, unit_fmt, gate=None, markers=None, ticks=None, label_w=150) -> str:
    """Horizontal single-series bars, value labels at the end, optional gate line and per-row marker (title = tooltip)."""
    w, row_h, top = 640, 22, 8
    plot = w - label_w - 70
    h = top * 2 + row_h * len(rows) + 18
    x = lambda v: label_w + plot * min(max(v, 0), vmax) / vmax  # noqa: E731
    parts = [f'<svg viewBox="0 0 {w} {h}" role="img">']
    for t in ticks or []:
        parts.append(f'<line class="grid" x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{top}" y2="{h - 18}"/><text x="{x(t):.1f}" y="{h - 4}" text-anchor="middle">{_e(unit_fmt(t))}</text>')
    for i, (label, v) in enumerate(rows):
        y = top + i * row_h
        parts.append(f'<text class="lbl" x="{label_w - 8}" y="{y + 15}" text-anchor="end">{_e(label)}</text>')
        if v is None:
            parts.append(f'<text x="{label_w + 4}" y="{y + 15}">n/a</text>')
            continue
        bw = max(x(v) - label_w, 1.5)
        parts.append(f'<rect class="bar" x="{label_w}" y="{y + 5}" width="{bw:.1f}" height="12" rx="2"><title>{_e(label)}: {_e(unit_fmt(v))}</title></rect>')
        parts.append(f'<text class="lbl" x="{label_w + plot + 8:.1f}" y="{y + 15}">{_e(unit_fmt(v))}</text>')  # a fixed value column: never under a tick
        for m in (markers or {}).get(label, []):
            mx, cls = x(m[0]), (m[2] if len(m) > 2 else "tick")
            parts.append(f'<line class="{cls}" x1="{mx:.1f}" x2="{mx:.1f}" y1="{y + 2}" y2="{y + 20}" stroke-width="2"><title>{_e(m[1])}</title></line>')
    if gate is not None:
        parts.append(f'<line class="gate" x1="{x(gate):.1f}" x2="{x(gate):.1f}" y1="{top}" y2="{h - 18}"><title>gate {gate}</title></line>')
    parts.append("</svg>")
    return "".join(parts)


def _chart(kind: str, data: dict) -> str:
    if kind == "rdi":
        groups = data["groups"]
        if not groups:
            return ""
        rows = [(g, v.get("rdi")) for g, v in groups.items()]
        markers = {g: [(v["random_rdi_expected"], f"random re-ranker {v['random_rdi_expected']:.2f}")] for g, v in groups.items() if v.get("random_rdi_expected") is not None}
        cap = f"Bars: RDI per lever group. Dashed line: the {data['gate']} gate. Tick: what a random re-ranker would give."
        return f"<figure>{_hbars(rows, 1.0, lambda v: f'{v:.2f}', data['gate'], markers, [0, 0.25, 0.5, 0.75, 1.0])}<figcaption>{_e(cap)}</figcaption></figure>"
    if kind == "recall":
        rows = [(s, (p or {}).get("rate")) for s, p in data["arms"] if isinstance(p, dict)]
        if not rows:
            return ""
        return f"<figure>{_hbars(rows, 1.0, lambda v: f'{v:.2f}', None, None, [0, 0.5, 1.0], 260)}<figcaption>Recall@pool, overall, per retrieval system (test split).</figcaption></figure>"
    if kind == "latency":
        flows = [f for f in data["flows"] if f[1] is not None]
        if not flows:
            return ""
        vmax = max(max(f[2] or 0, f[3] or 0) for f in flows) * 1.1
        markers = {f[0]: [m for m in ((f[2], f"p95 {f[2] / 1000:.2f} s", "tick"), (f[3], f"target p95 {f[3] / 1000:g} s" if f[3] else "", "gate")) if m[0]] for f in flows}
        rows = [(f[0], f[1]) for f in flows]
        return f"<figure>{_hbars(rows, vmax, lambda v: f'{v / 1000:.2f} s', None, markers)}<figcaption>Bars: median per flow (value at right). Solid tick: measured p95. Dashed tick: the NFR-01 target p95. Hover for values. Cart edits (milliseconds) are in the table.</figcaption></figure>"
    if kind == "overlap":
        ps, pairs = data["personas"], data["pairs"]
        n, cell, lab = len(ps), 34, 170
        size = lab + n * cell + 4
        parts = [f'<svg viewBox="0 0 {size + 130} {size}" role="img">']  # right margin: the rotated column labels
        for i, a in enumerate(ps):
            parts.append(f'<text class="lbl" x="{lab - 6}" y="{lab + i * cell + 21}" text-anchor="end">{_e(a)}</text>')
            parts.append(f'<text class="lbl" transform="translate({lab + i * cell + 20},{lab - 6}) rotate(-45)">{_e(a)}</text>')
            for j, b in enumerate(ps):
                v = 1.0 if a == b else pairs.get(f"{a} | {b}", pairs.get(f"{b} | {a}"))
                if v is None:
                    continue
                parts.append(f'<rect x="{lab + j * cell}" y="{lab + i * cell}" width="{cell - 2}" height="{cell - 2}" rx="2" '
                             f'style="fill:color-mix(in oklab, var(--seq-1) {v * 100:.0f}%, var(--seq-0))"><title>{_e(a)} / {_e(b)}: {v:.2f}</title></rect>')
        parts.append("</svg>")
        return f"<figure>{''.join(parts)}<figcaption>Top-3 overlap between personas on the same prompts (darker = more alike; 1.00 on the diagonal). Hover a cell for its value; the full list is in the table.</figcaption></figure>"
    if kind == "matrix":
        sc = data["per_scenario"]
        if not sc:
            return ""
        cells = "".join(f'<span class="chip {_e(v)}" title="{_e(k)}: {_e(v)}" style="margin:2px">{_e(k)} {_e(v)}</span>' for k, v in sc.items())
        return f"<figure><div>{cells}</div><figcaption>E10: status per pre-registered fault scenario (a scenario passes only if all its runs pass).</figcaption></figure>"
    return ""


def render_html(model: dict) -> str:
    s = model["summary"]
    body = [f"<h1>Zest evidence report</h1><p>Generated by <code>make report</code> from <code>eval/results/</code>, "
            f"<code>eval/headline.yaml</code> and <code>eval/thresholds.yaml</code>. No number on this page is typed by hand. "
            f"Repository HEAD <code>{_e(model['git'].get('head', ''))}</code>.</p>",
            f'<section class="status"><p><span class="chip {_e(s["overall"])}">{_e(s["overall"])}</span></p><ul>'
            + "".join(f"<li>{_md_inline(ln)}</li>" for ln in _header_lines(model)) + "</ul></section>"]
    for title, blocks in sections(model):
        body.append(f"<h2>{_e(title)}</h2>")
        for b in blocks:
            if b[0] == "p":
                body.append(f"<p>{_md_inline(b[1])}</p>")
            elif b[0] == "list":
                body.append("<ul>" + "".join(f"<li>{_md_inline(x)}</li>" for x in b[1]) + "</ul>")
            elif b[0] == "code":
                body.append(f"<pre><code>{_e(b[1])}</code></pre>")
            elif b[0] == "chart":
                body.append(_chart(b[1], b[2]))
            elif b[0] == "table":
                head = "".join(f"<th>{_e(c)}</th>" for c in b[1])
                rows = "".join("<tr>" + "".join(f"<td>{_md_inline(c)}</td>" for c in row) + "</tr>" for row in b[2])
                body.append(f'<div class="tbl"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>')
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>Zest Evidence Report</title><style>{CSS}</style></head><body><main>" + "".join(body) + "</main></body></html>\n")
