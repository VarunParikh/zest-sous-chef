# Prototyping Feedback: Zest AI Sous-Chef

This is what testing the prototype taught us, what we changed because of it, and what we would do next. Every row cites the evidence (an evaluation, a test or a hand test) and the decision (a conflict ID in `docs/core/open-conflicts.md`).

## 1. How the prototype was tested
| Method | When | What it covered |
|---|---|---|
| **Owner hand tests** in the browser, real models | Blocks 2.4 and 2.5 | YouTube links, open requests ("I am hungry", "surprise me"), personas, levers, the cart |
| **Automated tests** (`make test`, `make test-e2e`, `make test-embedder`) | Every story | Over 600 unit, contract and acceptance tests with fake models, plus 1 browser demo-path test and 1 embedder test |
| **Evaluations E1 to E14** with the real local models | Blocks 1.5, 2.6, 3.1 | Model choice, intent, vision, guard, retrieval, lever sensitivity, persona compliance, integrity, resilience, latency, traceability |
| **Spot checks**, assistant-made at the owner's direction (C67) | Block 3.1 | 20 reason lines, 103 catalogue variants |
| **Rehearsals** on the demo laptop | Block 3.4 | Pending: see section 5 |

## 2. What we learned and what changed
| Finding | Evidence | What changed | Decision |
|---|---|---|---|
| The guard classifier rated every bare YouTube link unsafe (S8) and "what should I eat" as specialised advice (S6), blocking the main flows | Block 2.4 and 2.5 hand tests | S6 verdicts are ignored; S8 is ignored only when the text has a YouTube link | C40, C44, C55 |
| Hunger and suggestion phrases ("I am hungry", "you suggest") and stove talk were redirected or read as smalltalk | Block 2.5 hand test | Hunger, suggestion and stove words added to the rules; intent prompt v2; meals steer the course | C43 |
| Open requests always returned the same few dishes, so levers looked inert | Block 2.5 hand test (the top dish changed in only 4 to 7 of 18 settings) | Open requests rank the whole course with the levers; no repeats in a session | C45 |
| The gourmet lever was inert for dishes, and β0 0.30 let price override organic everywhere | E6, E12 | Dish premium rescaled; pool 25; β0 0.20. E12 now passes; soft levers still below the E6 gate | C53, C57 |
| A rule that blocked injections also blocked ordinary diet requests, and did not generalise to new attacks | E4 on held-out `guard_v2` and `guard_v3` | The rule was narrowed; E4 accepted as a known limitation. Harm is limited by code (E7, E9) | C54, C55, C56 |
| "Healthy" echoed from a dish tag counted as a health claim | E13 | Health-claim words added to the reason validator; E13 now passes | C54 |
| A recipe line in an unsold unit took an out-of-stock pack | E7 adversarial arm | Allocation now prefers an in-stock pack (fixed test-first) | Block 2.6 (`77f99ca`) |
| Timeouts were documented as retried once, but the code never retried them | E10 pre-registration | The documents were changed to match the code: a retry would double the wait | C62, C66 |
| The trace could not explain latency per call | E11 planning | `llm_call` gained call kind and outcome; the guard and vision calls are traced too | C61 |
| 34 variants listed the wrong main ingredient; mushrooms counted as Jain-safe | SKU spot check | Validators V15 to V17, the catalogue fixed by rule, Jain excludes fungi; evaluations rerun with no status change | C68 |
| Five evaluation scripts silently dropped the post-hoc marker | Building the evidence report | Every save now records the reason; a test guards it | Block 3.2 |

## 3. What worked and what did not
**Worked:**
- **Code owns everything exact.** Guardrails after retrieval held across 11 personas: 0 violations in about 48,000 checks (E7). Prices and stock never came from the model: 0 mismatches in 200 random carts (E8).
- **Pre-registration and post-hoc discipline.** Datasets were hashed before runs, first results were kept, and held-out sets were added when a set had been seen. This is what exposed the guard's real generalisation (E4 on `guard_v3`), instead of a flattering score on a set the rules were tuned on.
- **Fallbacks.** Every injected fault took its defined message (E10, 26 of 26), and the samples path keeps the photo demo working when the local vision model is slow.

**Did not work well:**
- **Rule-based guarding against novel phrasings:** 0.55 on held-out attacks. Each new rule fixed the cases it was written for and missed new ones.
- **Soft levers through a top-3 view.** The weights and sliders change scores, but rarely the top three dishes (E6).
- **Local photo detection** on cluttered photos: recall 0.43 (E3).
- **A single author for data, labels and checks.** The spot checks found real defects, but they are not independent (C67).

## 4. Recommendations for the next iteration
1. **Guard:** add a classifier trained or prompted on held-out attack phrasings, and measure it on a set written by someone other than the rule author.
2. **Lever visibility:** show rank movement in the inspector (where each dish moved), not only the top 3, and test whether reviewers can see the soft levers' effect.
3. **Independent labelling:** have a second person label the photo set, the guard set and a sample of the catalogue.
4. **Larger evaluation sets:** at least 100 per class, so intervals separate pass from fail.
5. **Build the cut scope that matters most to users:** chat cart edits (FR-78), stock scenarios with demo controls (UJ22, C72), servings scaling (FR-32).
6. **Photo flow:** benchmark a larger local vision model (`qwen3-vl:8b`, not run by owner decision), or keep Gemini as an explicit opt-in.

## 5. Rehearsal feedback (block 3.4)
Pending. This section is filled in after the two rehearsals on the demo laptop (Test Plan §9), including the network-off test.
