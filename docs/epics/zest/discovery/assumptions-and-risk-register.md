# Assumptions and Risk Register: Zest AI Sous-Chef

Status: DRAFT v0.1 (awaiting owner approval) · Date: 2026-10-17
Weighting (owner input): the biggest threats are (1) the demo not working, (2) lack of technical depth, and (3) unsourced claims. The reviewer is a product leader who will also probe technical choices and expects decisions to be backed by data. The 3-day deadline is firm.

Scoring: Likelihood (L) and Impact (I) from 1 to 5; Score = L × I. 15 or more is Critical, 8 to 14 High, below 8 Medium.

## 1. Assumptions

| ID | Assumption | Why it matters | How we validate | When |
|---|---|---|---|---|
| A1 | A small local model on the 16 GB MacBook can extract ingredients and answer in acceptable time | Core chat flow | Day-1 benchmark (section 5) | Day 1 |
| A2 | Gemini free tier accepts image input and its rate limits are enough for at most 5 testers plus the demo | Photo flow | Read current limits; test 20 calls in a row | Day 1 |
| A3 | `youtube-transcript-api` works from the owner's home network for the demo videos | YouTube flow | Fetch all demo videos; keep fixtures regardless | Day 1 |
| A4 | A mock catalogue of at least 1,000 unique SKUs (unique by ingredient list and variant attributes) and about 34 dishes covers the Must journeys | Cart, engine, edge cases | Coverage script: every dish ingredient maps to a SKU or a deliberate gap | Day 1 to 2 |
| A5 | The reviewer accepts mock data and a simulated JioMart-style store | Scope | State clearly in the demo and limitations note | Day 3 |
| A6 | Levers apply from the next session (C4), and this is acceptable to the reviewer | Core promise | Visible UI hint; demo script shows it | Day 2 |
| A7 | Normalised weights (`w / Σw`) make slider effects visible enough to demonstrate | Core promise | Lever-sensitivity test on all personas | Day 2 |
| A8 | The owner's market research is accurate | Credibility | Source each claim (section 4) | Day 1 to 2 |
| A9 | Claude Code on the owner's current plan can complete the build within usage limits | Delivery | Check plan limits before Day 2; build in small chunks | Day 1 |
| A10 | A public GitHub repo is acceptable and contains no secrets or personal data | Delivery, privacy | Secret scan before every push | Daily |
| A11 | Gemini free-tier photo processing with user photos is acceptable once a notice is shown (C8) | Privacy | Notice in UI; documented in limitations note | Day 2 |
| A12 | Reviewer will judge both functionality and technical reasoning | Priorities | Decision Evidence Log (section 5) | Day 3 |
| A13 | The owner can run terminal commands with guided setup scripts | Setup | Setup script tested from a clean state; README walkthrough | Day 1 |
| A14 | The demo laptop has stable power and (ideally) internet; offline mode exists | Demo | Rehearsal on the actual machine | Day 3 |

## 2. Risk register

### 2.1 Critical and high risks (ordered by score)

| ID | Category | Risk | L | I | Score | Mitigation (before) | Contingency (if it happens) | Day |
|---|---|---|---|---|---|---|---|---|
| R1 | Demo | Local model too slow or inaccurate for extraction | 4 | 5 | **20** | Day-1 benchmark gate; smaller model; strict JSON schema; keep prompts short | Owner decided (2026-10-17) there is no cloud text fallback: drop to a smaller local model, shorten prompts, simplify the extraction schema; escalate to the owner on Day 1 if no local model passes the gate | 1 |
| R14 | Security | Gemini API key exposed (it was pasted in chat; repo will be public) | 4 | 5 | **20** | Rotate the key now; `.env` git-ignored; secret scan before commits; `.env.example` only | Revoke key; create new; rewrite history if ever committed | Now |
| R3 | Demo | YouTube transcript fetch blocked | 4 | 4 | **16** | Fixtures for 3 to 4 demo videos; fallbacks (title, paste) | Demo from fixtures; say so plainly | 1 |
| R8 | Delivery | Setup problems on a first-time terminal user | 4 | 4 | **16** | One-command setup and run scripts; guided walkthrough; test from clean state | Pair-debug with Claude Code; fall back to a prebuilt run script | 1 |
| R10 | Delivery | Time overrun against a firm 3-day deadline | 4 | 4 | **16** | Tiering and cut order (section 3); daily checkpoints; feature freeze Day 3 noon | Cut by the list; ship Must only | 1 to 3 |
| R12 | Credibility | Unsourced claims challenged | 4 | 4 | **16** | Claims ledger (section 4); source or soften; cite R-IDs | Remove or label "as supplied" | 1 to 2 |
| R18 | Delivery | Usage limits on the Claude plan throttle the build | 4 | 4 | **16** | Verify limits first; small, focused sessions; write specs so each step is short | Reduce scope; use local editor for manual steps | 1 |
| R4 | Demo | Hallucinated ingredient, SKU or price appears live | 3 | 5 | **15** | Catalogue grounding (P3); schema validation; golden test set | Tighten the schema, re-run the golden set, and demo only tested paths | 2 |
| R6 | Product | A lever shows no visible effect | 3 | 5 | **15** | Lever-sensitivity tests per lever group; score breakdown chart; choose demo prompts with clear divergence; control persona P9 | Adjust weights or data until effect is clear; document honestly | 2 |
| R11 | Credibility | Decisions not backed by data (model choice, MCP, framework) | 3 | 5 | **15** | Decision Evidence Log; benchmarks; ADRs listing alternatives | Present the measured limits and the reasoning | 1 to 3 |
| R2 | Demo | Gemini rate limit, outage or model rename | 3 | 4 | 12 | Model name in `.env`; bundled default sample photos with pre-computed results, labelled as samples | Switch to the labelled sample photos; say so plainly | 1 |
| R7 | Delivery | UI and engine do not integrate on Day 2 | 3 | 4 | 12 | Thin vertical slice first (one dish end to end); integrate daily | Cut features, keep the slice | 2 |
| R9 | Demo | Live demo conditions (Wi-Fi, memory pressure, cold model) | 3 | 4 | 12 | Warm-up step; close other apps; offline mode; health-check page | Backup screen recording | 3 |
| R17 | Data | Mock catalogue too thin, causing visible gaps | 3 | 4 | 12 | Build catalogue from the dish list; coverage script; regional synonyms (kothmir, kandha, batata) | Add SKUs; script stock-outs deliberately | 1 to 2 |
| R5 | Product | A guardrail fails (for example garlic for a Jain user) | 2 | 5 | 10 | Single tested guardrail module; filter before ranking; red-team set | Disable the dish; fix; re-run suite | 2 |

### 2.2 Medium risks

| ID | Category | Risk | L | I | Score | Mitigation |
|---|---|---|---|---|---|---|
| R13 | Privacy | Photo handling via Gemini free tier questioned | 3 | 3 | 9 | EXIF stripping; notice; limitations note; DPDP reference |
| R16 | Scope | Spec conflicts cause rework | 3 | 3 | 9 | Conflict log and precedence |
| R15 | Security | Prompt injection via transcript or photo text | 2 | 4 | 8 | Treat retrieved content as data (P4); test UJ57 |
| R19 | Ethics | Diet modes read as medical advice | 2 | 3 | 6 | Disclaimer; "simplified labels" wording |
| R20 | Repo | Messy public repo | 2 | 2 | 4 | Clean structure, README, CHANGELOG |
| R21 | Retrieval | Vector retrieval adds no measurable gain over lexical plus synonyms, so the added layer looks decorative | 3 | 3 | 9 | Day-1 three-way benchmark (lexical, vector, hybrid); record the result in the ADR whichever way it goes; keep FR-117 fallback |
| R22 | Retrieval | Wrong tag at 1,000+ SKUs (for example a non-Jain item tagged Jain) passes a guardrail | 3 | 5 | 15 | Rule-based validators on ingredient list versus tags; 10% manual audit; guardrail tests on every persona; hard filters run in code after retrieval |
| R23 | Platform | Embedding model plus Ollama text model exceed 16 GB RAM or slow the demo | 2 | 4 | 8 | Small ONNX embedder in the Chroma process; measure memory on Day 1; warm-up script; lexical fallback (FR-117) |
| R24 | Product | Candidate pool too small, so levers appear inert (the vector layer returns only what is displayed) | 3 | 5 | 15 | FR-111 pool larger than display set; AC-36 lever sensitivity test; inspector shows the pool |

## 3. Time-pressure cut order (Should and Could tiers)
If time runs short, cut in this order. The order protects technical depth and the core promise.
1. **UJ12** (learning from rejected upsell): invisible in a demo; cheapest to cut.
2. **UJ5** (chat-based cart editing): the cart UI already edits lines (B5).
3. **UJ22** (mid-chat stock-out): can be shown with a scripted stock-out instead.
4. **UJ8** (off-topic media): simple message, low risk.
5. **UJ21** (persona conflict): keep UJ7, which shows the same guardrail.
6. **UJ57** (indirect injection): cut last, because it signals security depth.
**Protected:** UJ11 (suggest-only pairing, the visible engine output), UJ60 (catalogue grounding) and UJ61 (confirm before destroying), because they are cheap and show technical judgement.
Could tier (UJ4, UJ16, UJ17, UJ24, UJ29): only if Must and Should are green.

## 4. Claims ledger (unsourced-claim control)

| Claim | Where used | Status | Action |
|---|---|---|---|
| Blinkit has recipe pages with ingredient ADD buttons | Research | Owner supplied two Blinkit recipe URLs; **could not be loaded in this session**, so unverified by us | Owner to confirm or add a screenshot |
| Blinkit uses Microsoft generative AI for recipe pages | Research | **Unsourced**: the supplied Blinkit pages would not be expected to say this | Find a news or press source, or label "as supplied" |
| Zepto has a recipe hub with festive collections | Research | **Unsourced**: the supplied Zepto page loaded empty; it is a product page for a recipe kit, which would not show a hub in any case | Find the hub page, or label "as supplied" |
| Zepto sells recipe kits | Research | Owner supplied a kit product URL; page loaded empty, unverified by us | Owner to confirm |
| Swiggy Instamart exposes an MCP server for AI assistants | Research | **Unsourced** (no source supplied) | Find Swiggy or Instamart documentation; it affects the MCP design decision |
| Shopvora is a third-party recipe-to-cart tool powered by Swiggy Instamart, with filters for diet, budget per plate, region and meal time | Research (new) | **Verified** on the Shopvora recipes pages (page text; not independently confirmed with Swiggy) | Cite; use as an analogue |
| JioMart recommends products from past purchasing habits | Research | **Verified** on the JioMart app page | Cite |
| JioMart has no prominent recipe-to-cart feature | Research | **Partly supported**: the JioMart app page describes no recipe feature but does describe a shopping-list tool that fills the cart | Cite carefully; avoid "has no recipe feature" |
| Gemini free tier content is used to improve Google products | Platforms, P9 | Verified on Google's pricing page | Cite |
| `youtube-transcript-api` v1.2.4 and IP-blocking warning | Platforms | Verified on PyPI | Cite |
| Burke 2002, Greshake 2023, Ji 2023, Mitchell 2019, Gebru 2021, Inan 2023, NIST AI RMF, OWASP LLM Top 10, DPDP Act 2023 | References | From knowledge | Check titles, years and DOIs |
| Gemini free-tier request limits | Platforms | Not yet read | Read before Day 1 test |

Rule: nothing goes in a demo or document as fact unless its row says "Verified" or is labelled "as supplied".

## 5. Decision Evidence Log (answers "why was X chosen?")
Each decision gets an ADR listing alternatives, the evidence, and the result. Evidence is produced by scripts in the repo, so the reviewer can re-run it.

| Decision | Alternatives | Evidence to collect | Output |
|---|---|---|---|
| Local text model | 2 to 3 small Ollama models; Gemini text as a reference | 10 recipe prompts: ingredient extraction F1, JSON validity rate, time to first token, total latency, memory use | `verify/benchmarks/text-models.md` |
| Vision approach | Gemini free tier vs local vision model | 15 sample photos: ingredient precision and recall, latency, failure rate | `verify/benchmarks/vision.md` |
| Guard design | Rules only; rules plus classifier (Llama Guard candidate) | 40 prompts in English and Hinglish: block rate, false-positive rate | `verify/benchmarks/guard.md` |
| Backend framework | FastAPI vs Node | Qualitative (fit with local-AI libraries), recorded in ADR | `design/adr/` |
| Retrieval approach (ingredient to SKU, intent to dish) | Lexical plus synonym table; small local embedding model; hybrid with embedded Chroma (chosen); networked vector database | **Revised by owner, 2026-10-17 (reverses the earlier "future scope" decision):** hybrid retrieval, with embedded Chroma and a local embedding model merged with lexical plus synonyms by reciprocal rank fusion, behind the `Retriever` interface. Reason for reversal: owner instruction to use a local vector database where one exists; an embedded store needs no service, and a 1,000-SKU catalogue with near-variants plus mood language is where lexical alone is weakest. Evidence to collect: recall at 5 on about 60 queries (ingredient, regional-name, mood) for lexical only, vector only and hybrid, plus index build time, memory and latency at 1,000 and 5,000 SKUs. If hybrid does not beat lexical, record it and let the owner decide the default | `verify/benchmarks/retrieval.md` |
| Variant selection | Fixed default variant per ingredient; lever-driven selection (chosen) | AC-38 and AC-39 sensitivity tests; cart-line explanations | ADR plus test report |
| Weight handling | Normalise vs clamp | Lever-sensitivity test on personas | ADR plus test report |
| Runtime MCP | Plain REST only; REST plus an MCP server over the mock store | **Decided by owner, 2026-10-17: no MCP; plain REST.** Rationale to record: scope, 3-day deadline, mock data only | ADR |
| Dev-time tools | GitHub CLI vs a GitHub MCP; Playwright for UI tests | Setup effort and reliability | ADR |

## 6. Demo reliability plan
1. **Health-check page** that shows each dependency (model loaded, Gemini reachable, transcript fixtures present).
2. **Warm-up script** that loads the local model before the demo.
3. **Default sample photos (owner decision, 2026-10-17):** there is no general replay mode. If live photo analysis fails, the app switches to bundled sample photos with pre-computed results, labelled as samples in the UI and the demo script, never presented as live.
4. **Backup screen recording** of the full happy path.
5. **Two rehearsals** on the actual laptop (Day 2 evening, Day 3 morning).
6. **Network-off test** to confirm the offline path.

## 7. Technical-depth showcase plan
Items that show engineering depth cheaply, and are already in scope: per-item score breakdown chart; automated guardrail and lever-sensitivity tests; an evaluation harness with a report; ADRs with measured alternatives; request tracing that shows each model call, schema validation and fallback; an architecture diagram.

## 8. Review cadence
Update this register at the end of each day: change scores, close or add risks, and log the cut decisions.

## 9. Sources
- NIST (2023), *AI Risk Management Framework 1.0*, NIST AI 100-1 (from knowledge; verify).
- OWASP, *Top 10 for LLM Applications* (from knowledge; verify).
- Project documents and platform checks cited in `docs/core/references-and-glossary.md`.
