# Known Limitations and Responsible-AI Note: Zest AI Sous-Chef

**Scope.** Zest is an interview prototype: a local, single-user demo on a mock grocery catalogue. This note says what it does not do well, what was not built, and how it handles data and risk.

**Sources.** Every number here comes from the evidence report (`../verify/report/report.md`), which is generated from `eval/results/` with no typed numbers. Every decision cites its conflict ID in `docs/core/open-conflicts.md`.

## A. Known limitations

### A1. Evaluations that did not meet their gate (accepted by the owner)
The overall evaluation status is **FAIL** under the Evaluation Plan §7 rule (C70). No FAIL is open and no critical failure was found; the four FAILs below were accepted by the owner as known limitations.

| Evaluation | What was measured | Result | Why it is accepted | Conflict |
|---|---|---|---|---|
| **E4 input guard** | Attacks blocked on a held-out set the rules never saw (`guard_v3`) | 11 of 20 attacks blocked (0.55; gate 0.90); 1 of 10 benign prompts wrongly redirected (gate ≤ 0.05) | The rules catch the phrasings they were written for and do not generalise. Harm is limited by design: no attack changed a cart end to end (E9, 0 of 36), and no ineligible item reached a persona (E7). Every cart change needs a tap the code checks; prices come only from the catalogue. Scores on the earlier sets are higher only because those sets were seen while writing the rules | C56 |
| **E2 intent classification** | Intent labels on 30 held-out utterances | 24 of 30 (0.80; gate 0.85; 95% interval 0.63 to 0.91, not separable from the gate) | No injection was ever labelled as a cart-changing intent. The stable errors are listed in `verify/benchmarks/block26.md` | C55 |
| **E6 lever sensitivity** | How often moving one lever group changes the top 3 (RDI; gate 0.33) | The hard filters pass clearly (diet 0.40, faith 0.74, specialised diet 0.93, add-on cap 0.73), and so do three history sliders. Most soft levers sit below the gate: the four weights 0.12 to 0.30, gourmet 0.07, cooling trend 0.05 | The soft levers do change rankings, but less than hoped. Gourmet and organic act mainly on which product variant is picked (E12 PASS). See the report §3 for every group | C57 |
| **E3 photo detection** | Local `qwen3-vl:4b-instruct` on 11 labelled photos | Precision 108/159 (0.68), recall 108/252 (0.43) on clear photos; p95 109.8 s | Owner decision: keep local-first (nothing leaves the laptop). Detections are labelled estimates and must be confirmed before the cart changes; labelled sample photos are the demo path and the fallback. **Photo accuracy is NOT MET** | C37 |

### A2. Behaviour you may notice
- **Over-strict guard on some ordinary phrases.** These are redirected as off-topic (MSG-REDIRECT):
  - a bare dish name the catalogue does not know ("make me ratatouille", "Shakshuka"; kept as a strict expected-failure test)
  - stove or oven instructions ("Switch off the oven after twenty minutes", W25 in E4)
  - Rephrasing with a food word usually works.
- **Retrieval quirk.** "Something cooling for a hot day" can suggest Hot Chocolate, because the keyword half of hybrid search matches "hot" (re-checked on 2026-10-19).
- **Vector similarity is about meaning, not shopping.** The add-on suggestions come from curated pairs plus similar dishes. "Similar" means similar descriptions, not "people who bought X also bought Y" (C17). There is no purchase data.
- **Reason lines may echo catalogue tags** such as "high protein". These come from the dish's tags, not from nutrition analysis (C68).
- **Chat cart edits are not supported.** "Remove the oil" replies MSG-UNSUPPORTED; edit in the cart window instead (FR-78 cut).

### A3. Data
- **All commerce data is mock.** Products, brands, prices, stock and nutrition are invented by a seeded generator (1,027 variants, 2,090 SKUs). Nothing comes from JioMart or any real store.
- **Labels and datasets were written by the assistant.** This covers ingredient tags, dataset labels and photo labels. The owner reviewed a sample only. The reason-line and SKU spot checks were also done by the assistant at the owner's direction, so they are not independent (C67). The SKU audit found 10 data-quality defects in 103 rows; they led to validators V15 to V17 and a rule-based fix (C68).
- **Dietary and faith rules are simplified.** Jain excludes meat, fish, egg, root vegetables, onion, garlic and (since C68) fungi; Satvik and other traditions vary more than these rules capture. **This is not dietary, religious, medical or allergy advice** (FR-15).
- **Small datasets.** n is 5 to 220 per evaluation, so most 95% intervals are wide.
- **English only.** Regional ingredient names are understood (for example kothmir, kandha), but code-mixed or regional-language prompts are untested.

### A4. Scope not built
| What | Status | Reference |
|---|---|---|
| Servings scaling | Cut; dishes are carted at their stored servings | FR-32 |
| Chat cart edits | Cut | FR-78, UJ5 |
| Learning from rejected add-ons | Cut | FR-65, UJ12 |
| Post-order pairing suggestion | Not built | US-27 |
| Live stock-out mid-chat and the demo stock and context controls | Cut; API endpoints 14 and 15 not built | UJ22, C72 |
| Other journeys | Deferred by the Product Strategy (§6.2), for example UJ13 to UJ15, UJ18 and UJ19, most of UJ25 to UJ56, UJ62 to UJ87 | Strategy §6.2 |
| Accounts, real payments, order tracking, persistence across refresh | Non-goals | Strategy §6.3 |

### A5. Platform and performance
- **Hardware.** Runs on an Apple-silicon Mac with 16 GB. The three local models need other apps closed: free RAM fell from 5.9 GB to 1.4 GB during the latency run (E11).
- **Measured latency** (server side, warm, 10 runs each; E11):
  - mood 1.2 s median, 1.25 s p95
  - text recipe 5.1 s, 5.5 s
  - YouTube 5.6 s, 11.0 s
  - photo upload 7.6 s, 12.5 s
  - sample photo 0.27 s, 0.33 s
  - The NFR-01 targets (ADR-002, ADR-003) were set from these same runs, so they are regression limits for this laptop, not user-research thresholds (C60).
- **Photo upload is the slow path.** E3 measured a 109.8 s p95 on its photo set, while E11 measured 12.5 s on the four demo photos. Larger or cluttered photos can take much longer; the timeout is 60 s, after which the sample photos are offered.
- **YouTube transcripts.** `youtube-transcript-api` is unofficial and may break or conflict with YouTube's terms (S-16). The demo videos also have saved fixtures, and the app falls back to them.
- **Timeouts are not retried** (C62). A slow model gives the defined fallback rather than a long wait.

## B. Responsible-AI note
Model-card style (Mitchell et al., 2019; R8).

**Intended use.** Demonstrating how explicit levers and coded guardrails steer an LLM-assisted grocery assistant, on a single laptop, with mock data, for review.

**Out of scope.** Real purchasing; dietary, allergy, religious or medical guidance; multi-user or public deployment; any non-mock data.

**Models** (all local through Ollama unless opted in):
| Role | Model | Decision |
|---|---|---|
| Intent, recipe extraction, reason line | `llama3.2:3b`, 4k context | ADR-002 |
| Input guard (after code rules) | `llama-guard3:1b` | ADR-006 |
| Photo detection | `qwen3-vl:4b-instruct` (default); Gemini 3.5 Flash-Lite, opt-in only | ADR-003 |
| Embeddings | Chroma's default all-MiniLM-L6-v2 | ADR-005 |

**What the models are allowed to do.** The models classify, extract and write one reason line. They never choose prices, SKUs, stock or eligibility: those come from code and the mock catalogue (ADR-004, ADR-008). The reason line is checked by a validator (length, no prices, no health-claim words) and replaced by a template if it fails.

**Data and privacy:**
- No accounts and no personal data are stored. Session state lives in memory and resets on refresh.
- **Photos.** EXIF and GPS data are stripped before analysis, and image bytes are never written to disk (T-102, T-103) or to the trace (T-109). By default the photo goes only to the local model; nothing leaves the laptop.
- **Gemini is off by default.** With the Gemini opt-in, the first upload shows: "Heads up: photos are sent to Google's Gemini free tier, which may use them to improve its products. Please don't upload personal photos. Continue?" Nothing is sent before consent (FR-50).
- **Trace log.** The local trace (`logs/trace.jsonl`, git-ignored) keeps only defined events, with user text cut to 120 characters.
- **Secrets.** The optional Gemini key lives only in a git-ignored `.env`. The repository and its full history are scanned for keys before each push (0 findings).

**Safety design:**
- Hard guardrails (diet, faith, allergy, stock) are filters in code that run after retrieval. E7 found 0 violations in 23,808 adversarial and 24,854 real-model checks.
- Text from videos, photos and pasted pages is treated as data, never instructions; injected instructions in transcripts are ignored (MSG-INJECT-DATA).
- No cart change happens without the user's tap, and destructive actions have a confirmation or Undo.
- Failures degrade to a defined message, never a false success (E10, 26 of 26 fault scenarios).

**Fairness:**
- Personas are chosen by the user and never inferred (FR-07).
- The optional gender cohort boost is set by the user and capped at 10% of one score component (S-14). It can still reflect stereotypes, so it is off unless chosen.

**Evaluation summary.** See the evidence report, which lists every evaluation, its pass rule, its result file and any post-hoc change. Human spot checks were limited, and were done by the assistant (C67).

**Caveats.** Everything in part A.
