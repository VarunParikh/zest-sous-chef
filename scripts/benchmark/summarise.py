"""Render verify/benchmarks/{retrieval,guard,text-models}.md from eval/results/*.json only
(Evaluation Plan §9: no number is typed by hand; a missing result shows NOT RUN)."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
RES, OUT = ROOT / "eval" / "results", ROOT / "docs" / "epics" / "zest" / "verify" / "benchmarks"


def load(prefix):
    return [json.loads(p.read_text()) for p in sorted(RES.glob(f"{prefix}-*.json"))]


def kn(p):
    if not p or not p.get("n"):
        return "NOT RUN"
    lo, hi = p["ci95"]
    return f"{p['k']}/{p['n']} ({p['rate']:.2f}; 95% CI {lo:.2f}–{hi:.2f})"


def env_line(rs):
    e = rs[0]["environment"] if rs else {}
    return f"Commit `{e.get('commit')}` (dirty: {e.get('dirty')}), {e.get('date')}, {e.get('platform')}, Python {e.get('python')}."


def retrieval():
    rs, sc, ad = load("E5"), load("E5_scale"), load("E5_addons")
    lines = ["# E5 Retrieval results (generated)", "", f"Split: test. {env_line(rs)} Notes: {rs[0]['notes'] if rs else ''}", "",
             "| System | Recall@pool overall | Mood | Ingredient | Regional | Variant | Recall@5 overall | MRR | Critical | Status |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rs:
        m = r["metrics"]
        lines.append(f"| {r['system']} | {kn(m['overall']['recall_at_pool'])} | {kn(m['mood']['recall_at_pool'])} | "
                     f"{kn(m['ingredient']['recall_at_pool'])} | {kn(m['regional']['recall_at_pool'])} | {kn(m['variant']['recall_at_pool'])} | "
                     f"{kn(m['overall']['recall_at_5'])} | {m['overall']['mrr']} | {len(r['critical_failures'])} | {r['status']} |")
    lines += ["", "## Scale (index build and query latency)", "", "| Embedder | Variants | Index ready (s) | Peak RSS (MB) | Query median (ms) | Query p95 (ms) |", "|---|---|---|---|---|---|"]
    for r in sc:
        for v in r["metrics"].values():
            lines.append(f"| {r['system']} | {v['variants']} | {v['index_ready_s']} | {v['peak_rss_mb']} | {v['query_ms_median']} | {v['query_ms_p95']} |")
    lines += ["", "## Add-on arm (ADR-004 v2)", "", "| Fusion | Curated pairs in top 5 | No-pair dish coverage | Non-companion coverage | Course rule (raw neighbours) | Persona breaks | Status |", "|---|---|---|---|---|---|---|"]
    for r in ad:
        m = r["metrics"]
        lines.append(f"| {r['system']} | {kn(m['curated_pair_recovery_top5'])} | {kn(m['no_pair_dish_coverage'])} | {kn(m.get('no_pair_non_companion_coverage'))} | "
                     f"{kn(m['course_rule_pass_raw_neighbours'])} | {len(r['critical_failures'])} | {r['status']} |")
    return "\n".join(lines) + "\n"


def guard():
    rs = load("E4")
    lines = ["# E4 Guard results (generated)", "", f"Split: test. {env_line(rs)}", "",
             "| System | Attack block rate (gate ≥ 0.90) | False positives (gate ≤ 0.05) | Status | Notes |", "|---|---|---|---|---|"]
    for r in rs:
        m = r["metrics"]
        lines.append(f"| {r['system']} | {kn(m.get('attack_block_rate'))} | {kn(m.get('false_positive_rate'))} | {r['status']} | {r['notes']} |")
    return "\n".join(lines) + "\n"


def text_rows(rs):
    out = []
    for r in rs:
        m = r["metrics"]
        if not m:
            out.append(f"| {r['system']} | NOT RUN | | | | | | {r['status']} |")
            continue
        out.append(f"| {r['system']} | {m['extraction_f1_mean']} | {kn(m['schema_valid'])} | {kn(m['quantity_accuracy'])} | {kn(m['invention_rate'])} | "
                   f"{m['free_ram_gb_after']} | {m['latency_ms_median']:.0f} / {m['latency_ms_p95']:.0f} | {r['status']} |")
    return out


def text_models():
    rs = load("E1")
    post = [json.loads(p.read_text()) for p in sorted((RES / "post-hoc").glob("E1-*.json"))]
    lines = ["# E1 Text-model results (generated)", "", f"Split: test (5 rows). {env_line(rs)}", "",
             "| Model | F1 mean (gate ≥ 0.80) | Schema-valid (gate ≥ 0.95) | Quantity accuracy | Invention rate (critical > 0.10) | Free RAM after (gate ≥ 3 GB) | Latency median / p95 (ms) | Status |",
             "|---|---|---|---|---|---|---|---|"]
    lines += text_rows(rs)
    if post:
        lines += ["", "## Post-hoc rerun (marked as such; first results above are unchanged)", "",
                  f"{env_line(post)} Context window {post[0]['metrics'].get('num_ctx')}; free RAM before load "
                  f"{post[0]['metrics'].get('free_ram_gb_before_load')} GB. Notes: {post[0]['notes']}", "",
                  lines[4], lines[5]] + text_rows(post)
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in (("retrieval.md", retrieval), ("guard.md", guard), ("text-models.md", text_models)):
        (OUT / name).write_text(fn())
        print("wrote", OUT / name)
