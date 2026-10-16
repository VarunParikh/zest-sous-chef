# Business Requirements Document (BRD): Zest AI Sous-Chef

Status: APPROVED v0.1 (owner, 2026-10-17) · Date: 2026-10-17
Inputs: product vision, Strategy, Platforms, Product Research, Personas, Risk Register, Settings Panel, User Journeys. Traceability IDs: B# (brief capabilities), UJ# (journeys), BR# (this document).

## 1. Purpose and background
Indian quick-commerce platforms treat recipe-to-cart as an engagement and basket-building lever (see Product Research), but most flows are page-based or search-based. Zest is a conversational assistant that converts a cooking intent into a compliant, correctly priced cart and exposes the recommendation logic as adjustable levers. This BRD states what the business needs and how success will be judged, at two levels:
- **Part A: Prototype validation objectives.** What must be demonstrated for the assessment, measured with mock data.
- **Part B: Product outcome hypotheses.** What a production version would aim to achieve. These are **beyond the MVP scope** and cannot be measured with mock data.

## 2. Stakeholders
| Stakeholder | Interest |
|---|---|
| Product owner (candidate) | A defensible, evidence-backed prototype and documentation set |
| Reviewer (product leader) | Functional correctness, technical soundness, decision rationale |
| End user (home cook, personas P1 to P11) | Fast, safe, relevant carts |
| Quick-commerce operator (hypothetical) | Basket value, conversion, trust, compliance |

## 3. Scope
In scope: capabilities B1 to B6; Must and Should journeys per Strategy section 6.2; mock catalogue; recommendation engine with lever panel; web UI. Out of scope: real platform integration, payments, accounts, persistence across refresh, voice, languages beyond English (with Marathi and Hindi ingredient names), production scale.

## 4. Part A: Prototype validation objectives

Targets are working values, confirmed in the Evaluation Plan after the Day-1 benchmark.

| ID | Objective | KPI and definition | Working target | Method and evidence |
|---|---|---|---|---|
| O1 | **Recommendation responsiveness** (levers materially steer output) | *Ranking Divergence Index:* 1 minus the overlap of the top-5 suggestions between baseline and altered lever settings for the same prompt, per lever group | At least 0.3 for each of the 7 lever groups; no lever group at 0 | Automated lever-sensitivity suite across personas P1 to P11, with Jordan (P9) as control; report in `verify/` |
| O2 | **Constraint compliance** (hard guardrails hold) | *Violation rate:* ineligible items appearing in carts or suggestions divided by all items shown, across persona × dish × entry-method combinations plus an adversarial set | 0 violations; at least 300 combinations evaluated | Guardrail test suite; red-team prompts in English and Hinglish |
| O3 | **Commerce data integrity** (grounded prices and SKUs) | *Reconciliation rate:* prices and SKU names in chat text that match the catalogue at render time | 100% | Automated reconciliation between chat output and cart state |
| O4 | **Intent-to-cart accuracy** | *Ingredient extraction F1* on a labelled recipe set; *photo detection precision and recall* on labelled photos; *pantry-delta correctness* (only missing items carted) | F1 at least 0.85; photo precision at least 0.80; delta correctness 100% on the test set | Evaluation Plan datasets; Day-1 benchmark |
| O5 | **Journey completion and resilience** | *Pass rate* of Must and Should journeys; *graceful-handling rate* on the edge-case set (correct, user-friendly fallback instead of error or silence) | Must 100%; Should at least 80%; edge-case at least 90% | Test Plan and Evaluation Plan |
| O6 | **Responsiveness** | *Text-to-cart latency* p50 and p95; *photo-to-suggestions latency* p50 and p95 on the demo machine | Set after the Day-1 benchmark (target: p95 within an interaction users tolerate for chat) | Benchmark script; recorded in ADR |
| O7 | **Engineering traceability and decision evidence** | *Trace coverage:* share of requirements linked to a story, a design element and a test; *decision evidence coverage:* share of consequential decisions with an ADR that lists alternatives and measured results | 100% and 100% | Traceability matrix; ADR set; Decision Evidence Log |
| O8 | **Responsible-AI posture** | Presence and consistency of consent notice, data-handling description, limitation statements and mock-data labelling across UI and documents | All present and consistent | Security and Privacy note; Responsible-AI note; UI review |

## 5. Part B: Product outcome hypotheses (beyond MVP scope)
These are hypotheses for a production version. They need live traffic and controlled experiments, so none is measurable or claimed in this prototype. No targets are set here; targets would come from a measured baseline.

| ID | Outcome | Metric definition | Why it matters |
|---|---|---|---|
| H1 | Recipe-to-cart conversion | Sessions that start with a recipe intent and end in a placed order, divided by such sessions | Core commercial value |
| H2 | Basket value | Average order value and items per order for Zest-assisted versus baseline sessions | Basket-building lever noted in the market research |
| H3 | Suggestion acceptance | Accepted pairing suggestions divided by shown suggestions, by category | Quality of the recommendation engine |
| H4 | Time to cart | Median time from first message to a built cart, compared with manual search | Convenience |
| H5 | Compliance trust | Dietary and faith compliance complaints per 1,000 orders | Safety and brand trust |
| H6 | Return usage | Share of users who start a second Zest session within a defined window | Habit formation |
| H7 | Ranking neutrality | Share of suggestions influenced by sponsored placement (should be zero or disclosed) | Trust, in light of retail-media pressure |

## 6. Business requirements

Priority: M = Must, S = Should. Each has acceptance criteria in Given/When/Then form.

| ID | Requirement | Priority | Source | Acceptance criteria |
|---|---|---|---|---|
| BR-01 | Accept four entry methods: YouTube link, text recipe (single or multiple messages), natural-language mood or intent, and photo | M | B1 to B4, UJ1, 2, 3, 6 | Given a valid input of each type, when sent, then the bot returns a dish plan and cart additions within the latency target |
| BR-02 | Build the cart by dish; a dish's cost equals the sum of its active ingredient lines; shared ingredients are not double-charged | M | Vision, DESIGN.md, UJ2 | Given two dishes sharing an ingredient, when both are carted, then one line is active and priced and the other is dimmed with an explanation; removing the active line transfers ownership |
| BR-03 | Photo flow treats the image as the user's available ingredients, suggests recipes, and carts only missing items | M | B4, UJ3 | Given a photo with items A and B and a recipe needing A, B, C, then only C is added |
| BR-04 | Provide the cart UI: top-right icon with badge, greyed and disabled when empty, per-dish and per-ingredient edit or remove, Buy Now, mobile-shaped window, order-placed message, 10-second auto-collapse with progress bar | M | B5 | Given an empty cart, then the icon is disabled; given items, then the badge shows the count; after Buy Now, the message appears and the window closes after 10 seconds with a visible progress bar |
| BR-05 | Provide levers that change recommendations; changes apply from the next chat session; effective weights are normalised | M | B6, Settings Panel, C4 | Given a lever change and a new session, when the same prompt is sent, then the Ranking Divergence Index meets O1; given a change mid-chat, then the UI states it applies next session |
| BR-06 | Enforce hard guardrails (diet, faith, specialised diet, allergens, stock, price cap) as filters applied before ranking | M | Settings Panel, UJ7, 21, 28 | Given any persona, then no ineligible item reaches the cart or a suggestion (O2) |
| BR-07 | Clear chat history and reset the engine independently of each other | M | Vision | Given clear chat, then levers are unchanged; given reset engine, then the chat is unchanged |
| BR-08 | Take all SKUs, prices and stock from the catalogue service; resolve stock-outs with user consent | M | UJ10, 22, 60, 64 | Given a model response naming a price or SKU, then the displayed value equals the catalogue value (O3); given a substitution, then the user confirms before the cart changes |
| BR-09 | Suggest, but never add, upsells and pairings | M | Constitution, UJ11 | Given a pairing suggestion, then the cart is unchanged until the user accepts |
| BR-10 | Handle edge cases gracefully: off-topic and injection input, videos without transcripts, regional ingredient names, unavailable ingredients, destructive actions | M | UJ9, 10, 20, 23, 57, 61 | Given each edge case in the Evaluation Plan, then the response is correct and friendly (O5) |
| BR-11 | Obtain consent before photo upload and label estimates and mock data | M | Constitution P8, P9 | Given the first upload, then a notice appears; given any estimate, then it is labelled |
| BR-12 | Deliver the full documentation set, traceability and reproducible evaluations on GitHub | M | Brief | Given the repo, then every requirement traces to a story and a test (O7) |
| BR-13 | Meet latency targets set after the benchmark | S | O6 | Given the demo machine, then p95 meets the ADR target |
| BR-14 | Conversational cart editing and rejected-suggestion handling | S | UJ5, 12 | Given an edit request in chat, then the cart updates after confirmation where needed |

## 7. Business rules
1. Eligibility is a hard filter: a violating item scores 0 and is never offered.
2. Persona values are set by the user and never inferred.
3. Uploaded photos are stripped of metadata and deleted after parsing unless the user opts in.
4. Order placement happens only through the Buy Now action.

## 8. Constraints, assumptions, dependencies
Constraints: 3-day deadline; free tools only; MacBook with 16 GB RAM; mock data only. Assumptions: A1 to A14 in the Risk Register. Dependencies: Gemini free tier for photos (fallback to labelled sample photos); `youtube-transcript-api` (fallback to fixtures); local model through Ollama (benchmark gate).

## 9. Traceability summary
| Objective | Requirements | Journeys |
|---|---|---|
| O1 | BR-05 | B6 |
| O2 | BR-06 | UJ7, 21, 28 |
| O3 | BR-08 | UJ60 |
| O4 | BR-01, BR-03 | UJ1, 2, 3 |
| O5 | BR-10, BR-14 | UJ9, 10, 20, 23, 57, 61 |
| O6 | BR-13 | all |
| O7 | BR-12 | n/a |
| O8 | BR-11 | UJ52 (partly) |

## 10. Approval
| Role | Name | Date | Decision |
|---|---|---|---|
| Product owner | | | |

## 11. Sources
Project documents; Burke (2002) for weighted scoring [R7]; NIST AI RMF 1.0 [R11] for the responsible-AI measures. See `docs/core/references-and-glossary.md`.
