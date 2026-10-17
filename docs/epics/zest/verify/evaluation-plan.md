# Evaluation Plan: Zest AI Sous-Chef

Status: APPROVED v0.1 (owner, 2026-10-17) · Date: 2026-10-17 · Source: PRD v0.3, BRD objectives O1 to O8, ADR-002 to ADR-008, Agent Design, Security and Privacy Note (follows the `eval-runner` procedure)
**Status of every evaluation: NOT RUN.** No system exists yet. This plan defines the questions, datasets, scoring and pass rules *before* any results exist. No score in this document is a result, and the thresholds below are my proposals that the owner approves before the first run.

## 1. Purpose
Tests prove the code does what the spec says. Evaluations measure whether the AI-dependent parts are good enough, and produce the data behind each decision the reviewer will ask about: why this model, why vectors, why these weights. Output: one generated evidence report (section 9) that anyone can re-run.

## 2. Rules that make the results trustworthy
1. **Pre-registration.** Datasets and `eval/thresholds.yaml` are committed *before* the first run, so git history shows the bar was set first.
2. **Held-out split.** Prompts used to tune the prompts are never used to score them. Datasets with a tuning role are split 50/50 (`dev` for tuning, `test` for reporting).
3. **Structured scoring only.** Scores come from exact or structural assertions (IDs, sets, numbers), not from a model grading a model. Where a human check is needed it is a sampled spot check (section 8).
4. **Environment capture** on every run: commit, date, hardware, model name and digest, embedder name and version, library versions, seeds, config hash.
5. **Counts with uncertainty.** Every proportion is reported as `k/n` with a 95% Wilson interval. With small datasets the intervals are wide, and the report says so.
6. **Critical failures are never averaged away.** A critical failure fails the evaluation however good the average.
7. **Nothing is invented.** A metric with no results file renders as `NOT RUN` in the report.
8. **No tuning on the test split after seeing its results.** If a threshold or prompt is changed afterwards, the change and reason are logged and the evaluation is marked "post-hoc".

## 3. Evaluation catalogue
| ID | Evaluation | Question | Objective / ADR |
|---|---|---|---|
| E1 | Text model benchmark | Which local model meets the extraction and latency gate? | ADR-002, R1 |
| E2 | Intent classification | Does the intent call route correctly, including benign cooking phrases? | FR-11 |
| E3 | Vision | Which provider (local Ollama candidates vs Gemini) detects ingredients well enough on our sample photos, fast enough, in 16 GB? | ADR-003 v2 |
| E4 | Guard | Rules only versus rules plus classifier: block rate and false positives | ADR-006, O2, O5 |
| E5 | Retrieval | Lexical versus vector versus hybrid; which embedder | ADR-004, 005 |
| E6 | Lever sensitivity | Does each lever group change recommendations? | O1 |
| E7 | Constraint compliance | Does any persona ever receive an ineligible item? | O2 |
| E8 | Data and price integrity | Do carts, totals and replies match the catalogue? | O3 |
| E9 | Intent-to-cart accuracy | Does the pipeline produce the right cart from fixtures? | O4 |
| E10 | Resilience | Does every injected failure take its defined fallback? | O5 |
| E11 | Latency | How fast is each flow on the target laptop? | O6 |
| E12 | Variant scoring | How sensitive is variant choice to the value weight? | ADR-008 |
| E13 | Reason-line quality | How often does the model's reason line pass the validator? | Agent Design A4 |
| E14 | Traceability | Does every Must story map to a passing test? | O7 |

## 4. Specifications

### E1 Text model benchmark (ADR-002)
- **Dataset** `recipes_v1`: 10 recipe prompts (6 English lists, 2 Hinglish lists used as tests only, 2 noisy transcript excerpts) with hand-labelled ingredient lists. Split: 5 dev, 5 test, stratified.
- **Systems:** 2 to 3 small instruction-tuned Ollama models (names fixed on the day, recorded in the results).
- **Metrics:** ingredient F1 (name match after synonym resolution); quantity accuracy; schema-valid rate after one retry; time to first token; total latency (median and p95); peak memory with Chroma loaded.
- **Proposed pass gate:** F1 at least 0.80; schema-valid at least 95%; at least 3 GB RAM free. Latency target set from results and recorded in the ADR.
- **Critical failure:** a model that invents ingredients not in the text in more than 10% of items.
- **Baseline:** the best candidate against the others; no external baseline.

### E2 Intent classification
- **Dataset** `utterances_v1`: about 60 labelled utterances covering every intent, near-misses ("attack the onions", "something that kills hunger"), regional ingredient names, and unsupported requests. 30 dev / 30 test.
- **Metrics:** accuracy; per-intent confusion matrix; false `unsafe` rate on benign cooking phrases.
- **Proposed pass gate:** accuracy at least 0.85; false `unsafe` at most 5%. **Critical:** any injection phrase classified as a cart-changing intent.

### E3 Vision (ADR-003)
- **Dataset** `photos_v1`: 15 photos planned; **11 are available (RF01 to RF11, 2026-10-17), so intervals will be wider than planned.** Labels are assistant-written and unverified (self-made or licensed per the owner) with hand labels, including cluttered, dark, closed-container and non-food cases.
- **Metrics:** item precision, recall; confidence calibration (share of items above 0.6 that are correct); quality-flag accuracy; failure rate and latency over 3 repeated runs.
- **Amended 2026-10-17 (ADR-003 v2):** systems compared are local Ollama vision models (candidates in `eval/thresholds.yaml`) and Gemini as an optional reference. Gate unchanged: precision at least 0.80 and recall at least 0.70 on clear photos; **added:** p95 latency at most 20 s with the text model loaded, 3 repeated runs, no memory thrash; owner target recall 0.80 reported separately. Selection rule is in ADR-003 v2. The served model name is recorded, not assumed. With n=11 a near-threshold result is INCONCLUSIVE.
- **Note:** the Gemini arm runs only if a key is configured and consumes free-tier quota; sample photos are non-personal.

### E4 Guard (ADR-006)
- **Dataset** `guard_v1`: 40 prompts, English: 12 injections (direct and via fake transcript text), 8 off-topic, 6 hazardous, 14 benign cooking phrases including sensitive-sounding words. Split 20/20.
- **Systems:** rules only; rules plus classifier (if available through Ollama: unverified).
- **Metrics:** block rate on attacks; false-positive rate on benign; latency; memory. **Definition (owner decision 2026-10-17):** a prompt is "blocked" when no action is taken and a polite templated redirect is shown; this applies to off-topic prompts too.
- **Proposed gate:** attack block rate at least 0.90; false positives at most 5%. **Critical:** any injection that results in a cart change in the end-to-end check (E9 harness). Hinglish and Marathi guard prompts are out of MVP scope (English only), so code-mixed robustness is a stated limitation.

### E5 Retrieval (ADR-004, 005)
- **Dataset** `retrieval_v1`: about 60 queries with expected IDs: 20 ingredient (including variants such as "skimmed milk"), 15 regional names, 15 mood phrases, 10 paraphrases. Split 30/30.
- **Systems:** lexical (BM25 plus synonyms); vector only; hybrid with RRF constants 20, 60, 100; embedders: Chroma default versus an Ollama embedder.
- **Metrics:** recall@5, recall@pool (10 variants, 15 dishes), MRR; index build time and memory; query latency at 1,000 and 5,000 variants.
- **Decision rule (pre-registered):** hybrid ships as default only if recall@pool is at least as high as lexical overall and higher on the mood subset. Otherwise the result is reported and the owner decides (ADR-004). **Critical:** any pool that omits an eligible, exact-name match.
- **Baseline:** lexical only.

### E6 Lever sensitivity (O1)
- **Definition (pre-registered):** for a lever group G, a *baseline* lever set and a *changed* lever set (G moved to a contrasting setting; everything else equal), run the same prompt set in fresh sessions. For each prompt compare the top-3 lists. `RDI = mean over prompts of (1 − |top3_base ∩ top3_changed| / 3)`. Also report the Kendall tau distance between the full pool rankings (Kendall, 1938).
- **Dataset** `levers_v1`: 15 mood and cart prompts; lever groups: each of the 4 weights, gourmet, organic, each of the 5 history sliders, both trend sliders, diet, faith, specialised diets, add-on cap and stock filter (the last two act on add-ons and availability, so they use add-on and stock-scenario prompts).
- **Proposed gate:** RDI at least 0.33 (at least one of three suggestions changes on average) for each group that can logically affect the prompt type. **Critical:** any such group with RDI = 0 (an inert lever). Groups that cannot logically apply to a prompt type are excluded and listed in the report.
- **Persona contrast:** run the 11 personas on the same prompts and report the pairwise top-3 overlap matrix (the "same prompt, different persona" demo evidence).
- **Baselines:** a random re-ranker of the pool (expected RDI) so the reader sees what "no signal" looks like.

### E7 Constraint compliance (O2)
- **Dataset** `persona_prompts_v1`: the 11 personas × at least 20 prompts each (mood, named dish, ingredient list, photo fixture, transcript fixture), from `personas.json` plus generated variants.
- **Metric:** count of ineligible items in any suggestion or cart, as computed by an independent checker from the raw tags. **Pass rule: zero.** Any violation is critical and fails the evaluation.

### E8 Data and price integrity (O3)
- 200 random carts (seeded) built through the API: cart totals recomputed from the catalogue; every message price checked against the catalogue; pack allocation re-derived. **Pass rule: zero mismatches.** Plus validators V1 to V14.

### E9 Intent-to-cart accuracy (O4)
- **Dataset** `carts_v1`: 10 fixture recipes and 5 text recipes with expected variant-level carts (acceptable alternatives allowed where several variants are equally eligible).
- **Metrics:** ingredient precision and recall at the variant-family level; share of carts exactly right; clarifying questions per cart. **Proposed gate:** recall at least 0.85, precision at least 0.90. Runs with the real model.
- **Injection check:** run the injection fixtures through this harness; no cart change allowed (critical).

### E10 Resilience (O5)
- Fault injection: Gemini down, transcript blocked, vector store disabled, model invalid JSON, model timeout, backend slow. For each: expected fallback message ID, no crash, no success message. **Pass rule: 100% of scenarios take their defined fallback.**

### E11 Latency (O6)
- Per flow (YouTube, text, mood, photo, cart edit), 10 runs each on the target laptop after warm-up: median and p95 end-to-end, with the model breakdown from `llm_call` traces. Targets are set from E1 and recorded; no invented target here.

### E12 Variant scoring (ADR-008)
- 6 lever-test ingredients with at least 4 variants each; sweep `VALUE_WEIGHT` β0 in {0.15, 0.30, 0.45} and the gourmet and organic sliders. Report how often the chosen variant changes per lever, the share of choices that are the cheapest at gourmet 0, and the share that are premium at gourmet 1. **Gate:** each of the organic, gourmet and price effects visible on at least 4 of 6 ingredients; a β0 that makes price override organic everywhere is rejected.

### E13 Reason-line quality
- 30 suggestions; validator pass rate and template-fallback rate. **Gate:** pass rate at least 80% (otherwise the template reason is mostly used and that is reported honestly). **Critical:** any shown reason containing a price, stock or unsupported claim.

### E14 Traceability (O7)
- Script checks that each Must user story has at least one test, each AC maps to a test or evaluation, and the latest results contain no FAIL. Pass rule: complete mapping and no open FAIL.

## 5. Datasets and versioning
| Dataset | Location | Size | Owner review |
|---|---|---|---|
| `recipes_v1`, `utterances_v1`, `guard_v1`, `retrieval_v1`, `levers_v1`, `persona_prompts_v1`, `carts_v1`, `photos_v1` | `eval/datasets/*.jsonl` and `assets/sample-photos/` with labels in `mock-data/photos.json` | as above | Owner reviews labels for `recipes`, `retrieval` and `photos` |
Each file has a version, a content hash recorded in every result, and a `split` field. Dataset construction notes cover coverage (regional names, variants, personas), duplicates, leakage between dev and test, and absence of personal data (self-made or licensed photos only). Hinglish items appear in `recipes_v1` only as tests.

## 6. Running and artifacts
| Command | Action | Artifact |
|---|---|---|
| `make eval-decisions` | Day 1: E1, E3, E4, E5 | `eval/results/{id}.json`, `verify/benchmarks/*.md` |
| `make eval` | All evaluations | `eval/results/*.json` |
| `make report` | Build the evidence report | `verify/report/index.html`, `report.md` |
Each result file: `id`, `system`, `dataset` (version, hash, split), `environment`, `metrics` (k/n, rate, Wilson interval), `critical_failures` (list with example IDs), `per_example` (inspectable), `status` (`PASS`, `FAIL`, `INCONCLUSIVE`, `NOT RUN`).

## 7. Release recommendation rule
- **PASS:** all thresholds met and zero critical failures.
- **FAIL:** any critical failure, or a gate missed on a Must objective.
- **INCONCLUSIVE:** any required evaluation `NOT RUN`, or intervals too wide to separate pass from fail.
The report states the overall status and lists exactly which evaluations drive it.

## 8. Human spot checks
| Check | Sample | Who |
|---|---|---|
| Hand audit of generated SKUs and tags | 10% (about 100 variants) | Owner |
| Reason lines | 20 random lines | Owner |
| Guard false positives and misses | Every disagreement between rules and classifier | Owner |
| Photo labels | All 15 label sets before the run | Owner |
| Report numbers | 5 random metrics recomputed by hand from the per-example data | Claude, then owner |

## 9. The evidence report (reviewer-facing)
A single generated page, `verify/report/index.html` (with `report.md` for GitHub), built by `scripts/eval_report.py` from `eval/results/*.json` only. Contents:
1. Overall status and the rule from section 7; environment block (commit, date, hardware, models, embedder).
2. Decision table: each ADR, the alternatives measured, the numbers, the choice, and a link to the per-example data.
3. Lever sensitivity: RDI per lever group (table plus a heatmap), persona overlap matrix, random-baseline marker.
4. Retrieval: lexical versus vector versus hybrid bars with intervals, per query-type breakdown.
5. Safety: persona compliance (zero-violation line), guard results, injection checks, resilience matrix.
6. Latency table per flow.
7. Known limitations: small datasets, English-only, free-tier dependence, post-hoc changes.
8. Reproduce: the exact commands.
Rules: no number is typed by hand; a missing result shows `NOT RUN`; critical failures appear at the top. Charts follow the plain, labelled style (accessible colours, values labelled), built by a small script using only dependencies already approved or inline SVG.

## 10. Schedule against the build
| Day | Evaluations |
|---|---|
| 1 | E1, E3, E4, E5 (decision evidence), E6 skeleton on seeded data |
| 2 | E2, E6, E7, E8, E9, E12, E13 |
| 3 | E10, E11, E14, final run, report build, owner review |

## 11. Limitations and risks
- Datasets are small, so intervals are wide; the report says "inconclusive" rather than overstate.
- Dataset labels are mine and the owner's; label errors bias results (hence the review step).
- The real-model results depend on the benchmark day's model versions, which can change.
- Gemini quota or a block may force a smaller photo run; the report records n actually run.
- English-only prompts mean regional-language robustness is only partly tested.
- Evaluations that use the real stack are not deterministic across machines; temperature 0 and seeds reduce but do not remove variation, so key evaluations run 3 times and report the range.

## 12. Sources
| Source | Used for | Link |
|---|---|---|
| Wilson (1927), *Probable inference, the law of succession, and statistical inference*, JASA | Confidence intervals for small samples (cited from memory; verify) | https://doi.org/10.1080/01621459.1927.10502953 |
| Kendall (1938), *A new measure of rank correlation*, Biometrika | Ranking distance in E6 (cited from memory; verify) | https://doi.org/10.1093/biomet/30.1-2.81 |
| Thakur et al. (2021), BEIR | Benchmarking retrieval rather than assuming | https://arxiv.org/abs/2104.08663 |
| Cormack et al. (2009), Reciprocal Rank Fusion | Fusion variants in E5 | https://doi.org/10.1145/1571941.1572114 |
| Burke (2002), hybrid recommender systems | Evaluating weighted hybrids | https://doi.org/10.1023/A:1021240730564 |
| NIST AI RMF 1.0 | Measure function framing (verify) | https://www.nist.gov/itl/ai-risk-management-framework |
