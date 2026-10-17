"""E5 retrieval benchmark (Evaluation Plan §4 E5; ADR-004 v2, ADR-005).

Systems: lexical, vector only, hybrid with k = 20, 60, 100, per embedder. Metrics per
query kind: recall@5, recall@pool, MRR. Critical: a pool that omits an exact-name match.
Add-on arm: curated only, vector only, fused 1:1, 2:1, 3:1.
Run: .venv/bin/python scripts/benchmark/retrieval.py [--split test] [--smoke --out DIR]
"""
import time

from _common import ROOT, parser, rows, save

from backend.catalogue.store import load_store
from backend.config import load_settings
from backend.engine.context import build_context
from backend.engine.eligibility import check_dish
from backend.engine.recommend import recommend_addons
from backend.evaluation.metrics import mrr, recall_at
from backend.evaluation.results import load_thresholds, make_result
from backend.evaluation.stats import proportion
from backend.retrieval.embedder import default_embedder
from backend.retrieval.retriever import Retriever
from backend.retrieval.vector import DISHES, VARIANTS, VectorStore
from backend.session.levers import LeverSet, merge_levers

POOL = {"mood": 15, "ingredient": 10, "regional": 10, "variant": 10}


def ranked(r: Retriever, vector, q: dict, system: str, store) -> list[str]:
    kind, text = q["kind"], q["query"]
    if system == "vector":
        if kind == "mood":
            return [h["id"].removeprefix("dish:") for h in vector.query(DISHES, text, POOL[kind])]
        hits = vector.query(VARIANTS, text, 20)
        if kind == "variant":
            return [h["id"].removeprefix("var:") for h in hits][: POOL[kind]]
        terms = []
        for h in hits:
            t = store.lexicon.canonical(store.variant(h["id"].removeprefix("var:")).ingredient_list[0])
            if t and t not in terms:
                terms.append(t)
        return [f"term:{t}" for t in terms][: POOL[kind]]
    if kind == "mood":
        return [h.id for h in r.dishes(text).hits]
    if kind == "variant":
        return [h.id for h in r.variants(text).hits]
    return [f"term:{h.id}" for h in r.resolve_ingredient(text).hits][: POOL[kind]]


def exact_name_terms(q: dict, store) -> set[str]:
    if q["kind"] not in {"ingredient", "regional"}:
        return set()
    word = q["query"].lower()
    return {f"term:{t}" for t, e in store.lexicon.entries.items() if word == t or word in e.aliases} & set(q["expected_ids"])


def run_system(name, r, vector, queries, store):
    per, crit = [], []
    for q in queries:
        t0 = time.perf_counter()
        got = ranked(r, vector, q, name, store)
        ms = (time.perf_counter() - t0) * 1000
        rel = set(q["expected_ids"])
        must = exact_name_terms(q, store)
        missing = sorted(must - set(got))
        if missing:
            crit.append({"query_id": q["query_id"], "missing_exact_name": missing})
        per.append({"query_id": q["query_id"], "kind": q["kind"], "top": got[:5], "hit_at_5": recall_at(got, rel, 5),
                    "hit_at_pool": recall_at(got, rel, POOL[q["kind"]]), "rr": mrr(got, rel), "latency_ms": round(ms, 1)})
    def agg(rows_):
        n = len(rows_)
        return {"recall_at_5": proportion(int(sum(x["hit_at_5"] for x in rows_)), n),
                "recall_at_pool": proportion(int(sum(x["hit_at_pool"] for x in rows_)), n),
                "mrr": round(sum(x["rr"] for x in rows_) / n, 4) if n else None,
                "latency_ms_median": sorted(x["latency_ms"] for x in rows_)[n // 2] if n else None}
    metrics = {"overall": agg(per), **{k: agg([x for x in per if x["kind"] == k]) for k in POOL}}
    return metrics, per, crit


def addon_arm(store, vector, settings, split_note):
    lev = LeverSet()
    ctx = build_context(settings=load_settings(env={"CONTEXT_NOW": "2026-10-17T19:00:00"}, env_file=None))
    personas = __import__("backend.catalogue.seed", fromlist=["load_personas"]).load_personas()
    out = []
    paired = sorted({p.dish_a for p in store.pairings})
    unpaired = [d.dish.dish_id for d in store.dishes if d.dish.dish_id not in paired and d.dish.dish_id != "D35"]
    for label, weights in [("curated_only", None), ("vector_only", "curated:0,vector:1"), ("1:1", "curated:1,vector:1"),
                           ("2:1", "curated:2,vector:1"), ("3:1", "curated:3,vector:1")]:
        env = {"ADDON_WEIGHTS": weights} if weights else {}
        s = load_settings(env=env, env_file=None)
        r = Retriever(store, None if label == "curated_only" else vector, s)
        rec_k = rec_n = 0
        for a in paired:
            top5 = [h.id for h in r.addons(a).hits[:5]]
            cur = [p.dish_b for p in store.pairings if p.dish_a == a]
            rec_k += sum(1 for c in cur if c in top5)
            rec_n += len(cur)
        covered = {d for d in unpaired if recommend_addons(d, lev, ctx, store, r).shown}
        cov = len(covered)
        mains = [d for d in unpaired if store.dish(d).dish.course not in s.addon_courses]
        crit = []
        for p in personas["personas"]:
            pl = LeverSet.model_validate(merge_levers(personas["defaults"], p["levers"]))
            for d in paired[:10] + unpaired[:10]:
                for sh in recommend_addons(d, pl, ctx, store, r).shown:
                    if not check_dish(store.dish(sh.candidate_id), pl, store, kind="addon").eligible:
                        crit.append({"persona": p["id"], "dish": d, "addon": sh.candidate_id})
        raw = [h for d in paired + unpaired for h in (vector.neighbours(d, 20) if label != "curated_only" else [])]
        course_ok = sum(1 for h in raw if store.dish(h["id"].removeprefix("dish:")).dish.course in s.addon_courses)
        out.append((label, {"curated_pair_recovery_top5": proportion(rec_k, rec_n),
                            "no_pair_dish_coverage": proportion(cov, len(unpaired)),
                            "no_pair_non_companion_coverage": proportion(len(covered & set(mains)), len(mains)),
                            "course_rule_pass_raw_neighbours": proportion(course_ok, len(raw)) if raw else None}, crit))
    return out


def embedder_for(spec: str):
    if spec == "chroma_default":
        return default_embedder(load_settings(env={}, env_file=None))
    provider, model = spec.split(":", 1)
    return default_embedder(load_settings(env={"EMBEDDING_PROVIDER": provider, "EMBEDDING_MODEL": model}, env_file=None))


def index_for(spec: str, store, settings, folder: str):
    path = settings.resolve(settings.chroma_path) if spec == "chroma_default" and folder == "main" else \
        ROOT / "data" / "chroma-eval" / f"{folder}-{spec.replace(':', '_')}"
    t0 = time.perf_counter()
    vector = VectorStore(path, embedder_for(spec))
    rebuilt = vector.ensure(store)
    return vector, {"embedder": vector.embedder.name, "index_rebuilt": rebuilt,
                    "index_ready_s": round(time.perf_counter() - t0, 1), "peak_rss_mb": peak_rss_mb()}


def peak_rss_mb() -> float:
    import resource
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20, 1)  # bytes on macOS


def latency_at_scale(store_small, spec, settings, queries, out, split, notes):
    """Index build time and query latency at 1,000 and 5,000 variants (ADR-004, 005)."""
    from backend.catalogue.store import GENERATED

    big_dir = next(GENERATED.glob("scale_*"))
    big = load_store(big_dir)
    metrics = {}
    for label, st in (("1000", store_small), ("5000", big)):
        vector, env = index_for(spec, st, settings, f"scale{label}")
        r = Retriever(st, vector, settings)
        lat = []
        for q in queries:
            t0 = time.perf_counter()
            (r.dishes if q["kind"] == "mood" else r.variants)(q["query"])
            lat.append((time.perf_counter() - t0) * 1000)
        lat.sort()
        metrics[label] = {"variants": len(st.variants), **env, "query_ms_median": round(lat[len(lat) // 2], 1),
                          "query_ms_p95": round(lat[min(len(lat) - 1, int(0.95 * len(lat)))], 1)}
    save(make_result("E5_scale", spec, "retrieval_v1.jsonl", split, metrics, [], [], "PASS",
                     notes=notes + "; latency is reported, not gated (targets come from E11)"), out)


def main():
    ap = parser(__doc__)
    ap.add_argument("--embedders", default="chroma_default,ollama:nomic-embed-text")
    ap.add_argument("--notes", default="")
    args = ap.parse_args()
    store, settings = load_store(), load_settings()
    t = load_thresholds()["E5_retrieval"]
    queries = rows("retrieval_v1.jsonl", args.split, args.smoke)
    split = "dev-smoke" if args.smoke else args.split
    notes = "smoke run: plumbing only, not a result" if args.smoke else args.notes
    lexical = Retriever(store, None, load_settings(env={"RETRIEVAL_MODE": "lexical"}, env_file=None))
    metrics, per, crit = run_system("lexical", lexical, None, queries, store)
    save(make_result("E5", "lexical", "retrieval_v1.jsonl", split, metrics, per, crit, "FAIL" if crit else "PASS",
                     env={"peak_rss_mb": peak_rss_mb()}, notes=notes), args.out)
    first_vector = None
    for spec in args.embedders.split(","):
        vector, env = index_for(spec, store, settings, "main")
        first_vector = first_vector or vector
        systems = [("vector", None)] + [(f"hybrid_k{k}", Retriever(store, vector, load_settings(env={"RRF_K": str(k)}, env_file=None)))
                                        for k in t["rrf_k_candidates"]]
        for name, r in systems:
            metrics, per, crit = run_system("vector" if name == "vector" else name, r, vector, queries, store)
            save(make_result("E5", f"{name}-{vector.embedder.name}", "retrieval_v1.jsonl", split, metrics, per, crit,
                             "FAIL" if crit else "PASS", env=env, notes=notes), args.out)
        if not args.smoke:
            latency_at_scale(store, spec, settings, queries, args.out, split, notes)
    ta = load_thresholds()["E5_addons"]
    for label, metrics, crit in addon_arm(store, first_vector, settings, split):
        ok = (metrics["curated_pair_recovery_top5"]["rate"] or 0) >= ta["curated_pair_recovery_top5_min"] and \
             (metrics["no_pair_dish_coverage"]["rate"] or 0) >= ta["no_pair_dish_coverage_min"]
        save(make_result("E5_addons", label, "retrieval_v1.jsonl", "pairings.csv", metrics, [], crit,
                         "FAIL" if crit or not ok else "PASS", env={"embedder": first_vector.embedder.name},
                         notes="dataset is pairings.csv and the dish pool (no labels); " + notes), args.out)


if __name__ == "__main__":
    main()
