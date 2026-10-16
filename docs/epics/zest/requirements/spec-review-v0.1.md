# Quality Review of the Product Spec v0.1

Date: 2026-10-17 · Reviewer: Claude (using the `analyze-spec` and `constitution-check` skills) · Method: document review only. No code exists yet, so no behaviour was tested.

## Part 1. Spec analysis (`analyze-spec`)

**Readiness decision: READY WITH CONDITIONS.** No blockers. Eight HIGH findings had to be fixed before stories could be written reliably. All were addressed in PRD v0.2; the status of each is in the table.

**Scope reviewed:** `product-spec.md` v0.1 against the BRD, Strategy, Constitution, Settings Panel, DESIGN.md and User Journeys.

### Findings

| ID | Severity | Where | Issue | Impact | Resolution | Status |
|---|---|---|---|---|---|---|
| F-01 | HIGH | FR-61, 62 | The four score components (pairing, history, trend, persona/gourmet) are not defined for dish options (mood, photo), add-ons or substitutes | Engine cannot be implemented or tested consistently; O1 unmeasurable | Added Appendix A with a definition per candidate type and tie rules | Fixed |
| F-02 | HIGH | FR-71, 73 | No rule for when two dishes share one pack versus need two packs; DESIGN.md says a 100 g butter pack is shared but two 200 g paneer needs become two packets | Wrong totals, cart disputes | Added combined-quantity rule: share a pack only if the combined need fits; otherwise add packs | Fixed |
| F-03 | HIGH | FR-60 | An allergen mask is required, but the MVP has no allergen input (UJ16 is Could) | Requirement with no source; implied safety claim | Allergens come only from chat declarations (Could); added FR-15 prohibiting safety assurances | Fixed |
| F-04 | HIGH | All external calls | No timeouts, retries or in-flight message rules | Hangs in the demo; duplicate requests | Added NFR-10 with initial timeout values (to be tuned by the benchmark) and input locking while processing | Fixed |
| F-05 | HIGH | Photo flow | No upload validation (type, size, count) | Crashes, abuse, cost | Added FR-57 | Fixed |
| F-06 | HIGH | FR-30 | "Detects a complete recipe" is untestable | Ambiguous multi-message behaviour | Rewrote: ingredients from each message are carted immediately under one open dish; the dish closes when a new dish, link or "new dish" arrives | Fixed (OQ-8) |
| F-07 | HIGH | FR-40, 41 | Mood flow said "select first"; owner decided the bot adds directly | Spec contradicted a decision | Rewrote: top-ranked eligible dish is added; two alternatives appear as one-tap swaps; undo | Fixed |
| F-08 | HIGH | Section 5.1 | Layout, chips, summary card, cart window and controls appear in prose only, with no IDs or acceptance criteria | Untraceable, untested | Added FR-100 to FR-104 and acceptance criteria | Fixed |
| F-09 | MEDIUM | `s_t` | Source of time, weekday and weather undefined | Non-reproducible trend effects | Appendix A: a context object from the system clock with a configuration override and mock weather label | Fixed |
| F-10 | MEDIUM | FR-60 | Behaviour when the stock filter is off undefined | Out-of-stock items could be bought | Items flagged out of stock; Buy Now blocked until swapped or removed (FR-83) | Fixed |
| F-11 | MEDIUM | Persona levers | Contradictory combinations (Jain faith with Non-Veg diet) undefined | Unpredictable filtering | FR-09: masks intersect; a warning shows | Fixed |
| F-12 | MEDIUM | FR-31 | Dish not in the recipe base undefined | Dead end | FR-33: ask for ingredients or offer the nearest dishes | Fixed |
| F-13 | MEDIUM | FR-20 | Accepted URL forms undefined | Unclear failures | FR-24: accept youtube.com/watch and youtu.be; otherwise a clear reply | Fixed |
| F-14 | MEDIUM | FR-13, 52 | Confidence threshold and ambiguity margin not set | Untestable | Initial config values stated, tuned by the benchmark | Fixed |
| F-15 | MEDIUM | NFR-04, 06 | Trace log might hold personal text or images | Privacy | Trace stores no images; user text truncated; local and git-ignored | Fixed |
| F-16 | MEDIUM | AC set | LLM non-determinism can make acceptance tests flaky | False failures | NFR-11: temperature 0, assert on structured output, tolerance rules for the Test Plan | Fixed |
| F-17 | MEDIUM | FR-32 | "Spices sub-linearly" has no formula | Ambiguous scaling | Priority lowered to Could; factors defined in the Data Model | Open |
| F-18 | MEDIUM | FR-80, 81 | No revalidation at checkout | Stale stock or price | FR-83 | Fixed |
| F-19 | LOW | Priorities | Mismatches with Strategy tiers (FR-23 vs UJ2 Must; FR-32 vs UJ4 Could; FR-65; FR-91; FR-92) | Scope drift | Aligned | Fixed |
| F-20 | LOW | FR-82 | Where a post-order suggestion is added is unclear | Confusion | A tap starts a new cart; the placed order is unchanged | Fixed |
| F-21 | LOW | FR-74 | Quantity bounds and money format undefined | Edge bugs | Quantity 1 to 9; whole-rupee display | Fixed |
| F-22 | QUESTION | FR-60 | Price cap applies to add-ons only; should dish options respect a budget (persona P10)? | Persona goal only partly served | Proposed: no, for the MVP | Open (owner) |
| F-23 | QUESTION | FR-07 | The gender cohort boost can encode stereotypes | Fairness | Capped, optional, documented in the Responsible-AI note | Accepted (OQ-6) |
| F-24 | MEDIUM | AC set | Many requirements lacked acceptance criteria | Gaps in verification | Added AC-21 to AC-34; the rest in the Test Plan | Partly fixed |

### Missing test scenarios (to go into the Test and Evaluation Plans)
Transcript with embedded instructions; safe cooking phrase that looks hostile ("attack the onions"); oversized or wrong-type upload; two dishes each needing 200 g paneer (two packs) versus shared butter (one pack); stock filter off; contradictory persona settings; dish not in the recipe base; message sent while processing; each timeout path; all weights at 0; Reset levers mid-session; mood with zero eligible dishes; mood swap and undo; Clear chat confirmation cancelled; stock change between cart and Buy Now; trace-log contents; focus trap in the cart window; ambiguous regional names (methi leaves or seeds); the same video pasted twice; quantity bounds.

### Dependencies and risks
Model and benchmark (R1), Gemini availability (R2), transcripts (R3), mock data validity (R17), non-deterministic outputs (F-16).

### Questions needing a decision
OQ-8 (multi-message recipe behaviour, now defaulted), initial timeout values, F-22 (budget for dish options).

## Part 2. Constitution check (`constitution-check`)

**Decision: PASS WITH CONDITIONS.** Rules were taken from `docs/core/constitution.md`; nothing was invented. Three failures and one gap were found and corrected in v0.2.

| Rule | Source | Status | Evidence |
|---|---|---|---|
| P1 Levers causal | Constitution Part 1 | PASS (after F-01) | FR-02, 08, 61; AC-02 |
| P2 Guardrails before ranking | P2 | PASS | FR-60 |
| P3 Catalogue is the only truth | P3 | PASS | FR-70, 79; AC-14 |
| P4 Retrieved content is data | P4 | **FAIL, fixed** | FR-12 was Should; the principle is non-negotiable. Now Must; the injection test scenarios stay Should |
| P5 Ask before destroying | P5, Authority Matrix | **FAIL, fixed** | FR-77 was Should and lacked undo for chat clears. Now Must with undo |
| P6 Honest about uncertainty | P6 | PASS | FR-14, 52 |
| P7 Graceful degradation | P7 | PASS WITH CONDITION | Timeouts were missing; NFR-10 added |
| P8 Mock data labelled | P8 | PASS | NFR-09, "Mock store" badge |
| P9 Privacy and consent | P9 (as amended) | PASS | FR-50, 51, 55; NFR-04 |
| P10 Traceability | P10 | UNKNOWN | Stories and the matrix are the next documents |
| P11 Scope discipline | P11, G1 | PASS WITH CONDITION | Priorities aligned to Strategy (F-19) |
| Authority: substitution needs user confirmation | Matrix 3.1 | **FAIL, fixed** | FR-76 was Should while FR-62(c) was Must; now Must |
| Authority: no safety assurances for allergy or medical | Matrix 3.1 | **Gap, fixed** | FR-15 added |
| Authority: bot never changes persona | Matrix 3.1 | PASS | FR-07, 90 |
| Authority: order only by user action | Matrix 3.1 | PASS | FR-80 |
| G5 LLM usage (schema, retry, config) | Build guardrails | PASS | FR-21; NFR-07, 11 |
| G2, G3, G6 to G8 | Build guardrails | NOT APPLICABLE at spec stage | |

**Conflicts:** C11 (mood flow) resolved by the owner in favour of the brief.
**Missing documents:** none.
**Limits of this check:** document review only; no repository code exists.

> Note (2026-10-17): this review covers PRD v0.1. PRD v0.2 and v0.3 were produced afterwards; v0.3 (hybrid retrieval, section 6.12) has not been re-reviewed. See PRD section 17.
