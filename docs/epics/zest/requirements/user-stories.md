# User Stories and Traceability Matrix: Zest AI Sous-Chef

Status: **APPROVED v0.6 (owner, 2026-10-22, with the Zest 2.0 plan): section M adds US-42 to US-47 (onboarding).** v0.5 was **APPROVED v0.5 (owner re-approved 2026-10-18) (2026-10-18): C37 doc-sync to ADR-003 v3 (local `qwen3-vl:4b-instruct` default, Gemini opt-in, samples for the demo and as fallback). ** v0.4 was APPROVED (owner, 2026-10-18), re-approved after the C15 sync to the ADR-003 Day-1 decision.** v0.3 was APPROVED (owner, 2026-10-17) (v0.2 was approved earlier the same day; v0.3 changes US-19 only, to sync with ADR-004 v2 and PRD v0.4) · Date: 2026-10-17 · Source: PRD v0.4, BRD, Strategy
Sizing: S = under 1 day, M = 1 to 2 days, L = 2 to 3 days of build effort. The playbook allows 1 to 5 days; the 3-day deadline means each story here is kept to 3 days or less and the parallel work is stated in the Strategy plan. Priority follows PRD (M/S/C). Every story states acceptance criteria (AC) as Given/When/Then, and test IDs are assigned in the Test Plan (document 19).

Format: **US-xx** As a *persona*, I want *capability*, so that *benefit*. Covers: FR/AC.

## A. Session and levers
**US-01** As Rohan (P7 reviewer), I want lever changes to apply from my next chat session, so that I can compare outcomes cleanly. *M · M* Covers FR-01, 02, 03; AC-01.
- Given levers changed mid-session, when I send the same prompt, then results match the snapshot and the banner shows.
- Given Clear chat after the change, when I send it again, then the new levers apply.

**US-02** As Alex (P7), I want four independent weight sliders with effective percentages, so that I can see exactly how the mix changes. *M · M* Covers FR-06, 08, 104; AC-03.
- Given weights 80/80/40/0, when I view the panel, then shares show as 40/40/20/0 percent.
- Given all weights 0, when the engine runs, then defaults return with a notice.

**US-03** As a user, I want Clear chat and Reset levers to act independently, so that I never lose work by accident. *M · S* Covers FR-04, 05; AC-18, 19.
- Given a non-empty cart, when I press Clear chat, then I must confirm; Cancel changes nothing.
- Given Reset levers, then chat and cart are unchanged.

**US-04** As Priya (P6), I want to set my persona myself and have contradictory settings flagged, so that the bot never guesses who I am. *S · S* Covers FR-07, 09; AC-25.
- Given Jain faith with Non-Veg diet, then a warning shows and masks intersect.
- Given gender not set, then no cohort boost applies.

## B. Input safety and understanding
**US-05** As the product owner, I want off-topic and injection input redirected, so that the bot stays safe and on task. *M · M* Covers FR-10, 11, 12; AC-15, 21, 22.
- Given "Forget all previous instructions…", then the standard redirect appears and nothing is carted.
- Given "attack the onions", then the message is processed normally.
- Given a transcript that contains instructions, then they are ignored and not carted.

**US-06** As Meera (P1), I want regional names such as kothmir and kandha understood, so that I can write the way I speak. *M · M* Covers FR-13; AC-17.
- Given "kothmir, kandha, batata", then Coriander Leaves, Onion and Potato are resolved.
- Given an ambiguous name (methi), then one short clarifying question is asked.
- Given the vector store is off, when I name ingredients, then the same names resolve through the lexical retriever (FR-117).

**US-07** As a user, I want estimates and safety limits stated honestly, so that I can trust the bot. *M · S* Covers FR-14, 15.
- Given a detected quantity, then it is labelled an estimate.
- Given "is this safe for my nut allergy?", then the bot gives no assurance and says labels are simplified.

## C. YouTube flow
**US-08** As Meera (P1), I want to paste a recipe video link and get a cart, so that I skip transcribing ingredients. *M · L* Covers FR-20, 21, 24; AC-07, 16, 31.
- Given the demo Paneer Butter Masala link, then ingredients are extracted, mapped to SKUs and carted at catalogue prices.
- Given the transcript fetch fails, then fixture, then title and description, then a paste prompt.
- Given the same link twice, then the dish is not duplicated and I am asked.

**US-09** As a user, I want sponsor talk and non-recipe videos ignored, so that my cart holds only food. *S · S* Covers FR-22.
- Given a video without recipe context, then the off-topic reply appears.

**US-10** As Meera (P1), I want a second link to merge shared ingredients and ask about staples, so that I do not double-buy. *M · M* Covers FR-23; AC-08, 24.
- Given two dishes needing butter within one pack, then one pack is carted and the second line is dimmed.

## D. Text recipe flow
**US-11** As Imran (P3), I want to type a recipe over several messages, so that I can describe it naturally. *M · M* Covers FR-30, 31, 33; AC-26.
- Given three messages listing ingredients for one dish, then each is carted immediately under one open dish.
- Given "new dish", then the open dish closes.
- Given a dish not in the recipe base, then ingredients are requested or nearest dishes offered.

**US-12** As a user, I want servings to scale quantities, so that the cart matches how many I cook for. *C · S* Covers FR-32. (Could; first to cut.)
- Given "for 4", then quantities scale and the scaling is stated.

## E. Mood flow
**US-13** As Karan (P5), I want to say "I am feeling indulgent" and have the bot add a suitable dish, so that I do not have to decide. *M · L* Covers FR-40, 41, 42; AC-09, 29, 30.
- Given the message, then the top eligible dish is carted with a one-line reason and two swap options appear.
- Given a swap tap, then only that suggestion's dish is replaced; earlier items are untouched.
- Given Undo, then the cart returns to its prior state.
- Given no eligible dish, then the reason is stated and the cart is unchanged.

## F. Photo flow
**US-14** As Ananya (P4), I want a clear privacy notice before I upload, so that I choose with informed consent. *M · S* Covers FR-50, 51; AC-34.
- Given first upload with live analysis enabled (opt-in Gemini), then the Gemini notice appears and metadata is stripped and the photo deleted after parsing. With the default local vision model or a sample photo, no photo leaves the laptop.

**US-15** As Lakshmi (P8), I want to photograph my kitchen and get dishes I can finish, so that I buy only what is missing. *M · L* Covers FR-52, 53, 54, 57; AC-10, 23.
- Given a photo of paneer and capsicum, then three dishes are ranked and the top dish's missing items only are carted.
- Given low-confidence items, then I am asked to confirm.
- Given a wrong file type or over 5 MB, then it is rejected with a reason.

**US-16** As the owner, I want a labelled sample-photo fallback, so that the flow works by default and when live analysis does not. *M · S* Covers FR-55, 56; AC-11.
- Given the local vision model (default) or the opt-in Gemini fails or times out, then sample photos are offered and labelled as samples.
- Given a non-food photo, then the "couldn't spot any ingredients" reply appears.

## G. Recommendation engine
**US-17** As Alex (P7), I want lever changes to visibly change recommendations, so that I can verify the engine is real. *M · L* Covers FR-60, 61, 62, 66, 67; AC-02, 06.
- Given a changed lever group and a new session, then the Ranking Divergence Index meets the objective.
- Given equal scores, then ties break by `s_p` then ID, reproducibly.

**US-18** As a user, I want a "Why this?" view, so that I understand each suggestion. *M · M* Covers FR-63, 104; AC-20.
- Given a suggestion, then the component contributions are listed and sum to the displayed score; the panel shows the stacked chart.

**US-19** As Meera (P1), I want add-on suggestions that I must tap, so that I am never upsold silently. *M · S* Covers FR-62, 64, 82, 118, 119; AC-43 to AC-45.
- Given an add-on suggestion, then the cart changes only after my tap.
- Given a dish with no curated pairing, when it is carted, then at least one eligible companion-course add-on is still offered (from vector neighbours), and none breaks my persona.
- Given the vector store is unavailable, then add-ons are still offered from the curated pairings and no error is shown.

**US-20** As a user, I want rejected add-ons to reduce similar suggestions this session, so that the bot learns from me. *C · S* Covers FR-65. (Could.)

**US-37** As Karan (P5), I want "something cooling" or "feeling indulgent" understood by meaning, so that I do not have to know dish names. *M · L* Covers FR-110, 111, 112; AC-35, 36, 37.
- Given a mood phrase with no keyword match, then relevant dishes appear in a pool of at least 15, guardrails remove ineligible ones after retrieval, and the levers rank the rest.

**US-38** As Alex (P7), I want the engine's levers to choose among product variants, so that I see the effect in my cart. *M · M* Covers FR-113, 114, 116; AC-38, 39, 42.
- Given "milk" with organic high versus low, then different eligible variants are carted and the line explains the choice.
- Given "milk" with gourmet affinity 0 versus 1, then a cheaper variant is carted at 0 and a premium one at 1 (price carries weight, FR-113; AC-42).
- Given "skimmed milk", then only skimmed variants are eligible; the cart line offers switching to another eligible variant.

**US-39** As Alex (P7), I want a retrieval and scoring inspector, so that I can see candidates, similarity, eligibility and final score. *M · M* Covers FR-115; AC-41.

**US-41** As a reviewer with a clean MacBook, I want to open one downloaded app and have Zest set itself up, so that I can try it without installing Python, Node, Homebrew or Ollama. *S · M* Covers NFR-08; ADR-011.
- Given a clean Apple-silicon Mac on macOS 14 or newer, when I open `Zest.app` from the DMG (after the one-time Gatekeeper "Open Anyway"), then a setup page shows each missing model downloading and opens Zest when all are present, with no terminal step.
- Given an Ollama server already running on port 11434 with all three models, when I open the app, then Zest uses it and downloads nothing.
- Given an Intel Mac or macOS older than 14, when I open the app, then a dialog says why it cannot run and nothing starts.
- Given the app is running, when I choose Quit Zest, then the API server and any Ollama server the app started both stop.

**US-40** As the owner, I want retrieval to degrade to lexical matching if the vector store fails, so that the demo never breaks. *M · S* Covers FR-117; AC-40.

## H. Catalogue and cart
**US-21** As Meera (P1), I want prices and stock to come from the store, never invented, so that the total is correct. *M · M* Covers FR-70, 71, 79; AC-14, 24.
- Given a model reply with a different price, then the catalogue price is shown.
- Given two 200 g paneer needs, then two packs are carted.

**US-22** As Meera (P1), I want to see my cart grouped by dish with totals, so that I understand the cost. *M · M* Covers FR-72, 73, 74.
- Given dishes in the cart, then each dish total equals its active lines; I can remove a dish, a line, or change a quantity (1 to 9).

**US-23** As a user, I want a cart icon with a badge that is disabled when empty, so that state is obvious. *M · S* Covers FR-75; AC-12.

**US-24** As Imran (P3), I want a stock-out handled with a proposed substitute, so that I choose the replacement. *M · M* Covers FR-76, 83; AC-28, 33.
- Given a stock-out, then a substitute with price and flavour difference is proposed and the cart changes only on accept.
- Given stock drops to zero before Buy Now, then the order is blocked until I swap or remove.

**US-25** As a user, I want chat cart edits and confirmed destructive actions, so that I stay in control. *S/M · S* Covers FR-77, 78.
- Given "clear my cart" in chat, then a confirmation and Undo are offered.

## I. Checkout
**US-26** As Meera (P1), I want Buy Now to place one order and confirm it, so that I know it worked. *M · M* Covers FR-80, 81; AC-13.
- Given Buy Now, then the order-placed message with a progress bar shows in the same window and closes after 10 seconds; the cart is empty; a second press does nothing.

**US-27** As a user, I want one pairing suggestion after ordering, so that I discover a companion. *S · S* Covers FR-82. A tap starts a new cart; the placed order is unchanged.

## J. Persona guardrails
**US-28** As Rohan (P2) and Ananya (P4), I want requests that break my diet intercepted, so that I never receive them. *M · M* Covers FR-90; AC-04, 05.
- Given Jain asking for Garlic Bread, then no garlic is carted and a compliant alternative is offered.
- Given Pure Veg and a chicken video, then the mismatch is flagged and a vegetarian version offered.

**US-29** As Priya (P6), I want hidden animal-derived ingredients caught, so that "looks vegan" is checked against tags. *S · M* Covers FR-91.

**US-30** As Rahul (P10), I want a recipe with unavailable ingredients reported with alternatives, so that I know what I can make. *S · S* Covers FR-92.

## K. Interface and accessibility
**US-31** As a user, I want a split screen with chat and levers that adapts below 1024 px, so that it works on my laptop. *M · M* Covers FR-100, 101; NFR-03.
**US-32** As a user, I want the input locked while Zest is thinking, so that I cannot send duplicates. *M · S* Covers FR-102; AC-27.
**US-33** As a keyboard user, I want the cart window to trap focus and close with Escape, so that I can operate it without a mouse. *M · S* Covers FR-103; AC-32.

## L. Platform quality
**US-34** As the owner, I want every external call to time out and fall back, so that the demo never hangs. *M · M* Covers NFR-02, 10; section 9.
**US-35** As the reviewer, I want a trace log with no personal data, so that decisions can be audited. *M · S* Covers NFR-06; AC-34.
**US-36** As the owner, I want a seeded, validated catalogue of at least 1,000 unique SKUs and a one-command setup, so that anyone can reproduce the demo. *M · L* Covers NFR-08, 09, 12, 13; mock-data plan.
- Given the generator, then every tag agrees with its SKU's ingredient list, every dish ingredient resolves, and the 5,000-SKU set builds with the same code.

## M. First-use onboarding (Zest 2.0)
**US-42** As a user, when I change a lever I want one click to apply it and rerun my last request, so that I see how the change affects the pick. *S · M* Covers FR-120; AC-46 to AC-49.
- Given a carted suggestion, when I change a lever and press Apply and rerun, then a new session starts with my new levers and my last request is sent again; if my cart had items I confirmed first.

**US-43** As a first-time user, I want to pick who I'm cooking for from cards, so that I understand each persona at a glance. *S · M* Covers FR-121; AC-50, AC-51.
- Given the persona cards, when I press Use this persona on Meera Shah, then her levers are set and her card reads "Jain: no root vegetables, onion, garlic or mushrooms".

**US-44** As a first-time user, I want each lever explained in plain words, so that I know what moving it does. *S · S* Covers FR-122; AC-52, AC-53.
- Given any lever, when I hover, focus or tap its ⓘ, then I read what it changes and whether it is a Rule or a Preference.

**US-45** As a first-time user, I want to ask "what can I say?" and get examples I can tap, so that I can start in one click. *S · S* Covers FR-123, FR-124; AC-54 to AC-57.
- Given a new chat, when I type "what can I say?", then Zest lists the four ways in with examples that act on one tap; the greeting chips also act on one tap.

**US-46** As a first-time user of the Mac app, I want to learn how Zest works while the models download, so that I'm ready when it opens. *C · S* Covers FR-125; AC-58, AC-59.
- Given the first launch, when models are downloading, then a short introduction plays under the progress bars and Zest still opens as soon as the models are ready.

**US-47** As a first-time user, I want a short, skippable tour of the main screen, so that I know where to start. *S · M* Covers FR-126; AC-56, AC-60, AC-61.
- Given my first visit, when the main screen opens, then a five-step tour starts; I can skip it, and the help icon in the top-right corner starts it again.

## Traceability matrix (objectives to stories)
| Objective | BR | FR | Stories | AC | Tests |
|---|---|---|---|---|---|
| O1 Ranking divergence | BR-05 | FR-01 to 08, 61 to 67, 111, 113 | US-01, 02, 17, 18, 37, 38, 39 | AC-01 to 03, 20, 36, 38 | T-001 to 004, 030 to 038, 034; E6 |
| O2 Constraint compliance | BR-06 | FR-09, 60, 90 to 92, 15, 112, 116 | US-04, 07, 28 to 30, 37 | AC-04 to 06, 25, 37 | T-010 to 022, 070 to 074; E7 |
| O3 Data integrity | BR-08 | FR-70 to 79, 83 | US-21 to 25 | AC-08, 14, 24, 28, 33 | T-050 to 062, 100, 101; E8 |
| O4 Intent-to-cart accuracy | BR-01, BR-03 | FR-20 to 57, 110 | US-06, 08 to 16, 37 | AC-07, 09, 10, 16, 17, 26, 35 | T-080 to 092; E9 |
| O5 Journey resilience | BR-10, BR-14 | FR-10 to 12, 55, 117, NFR-02, 10 | US-05, 16, 34, 40 | AC-11, 15, 21 to 23, 40 | T-042, 070 to 072, 090, 091; E10 |
| O6 Responsiveness | BR-13 | NFR-01, 10 | US-34 | Benchmark ADR | E1, E11 |
| O7 Traceability | BR-12 | NFR-06 | US-35 | AC-34 | E14 |
| O8 Responsible AI | BR-11 | FR-07, 14, 15, 50, 51 | US-04, 07, 14 | AC-34 | T-102, 103, 109; E3 |

Zest 2.0 onboarding (US-42 to US-47) answers reviewer feedback rather than a BRD objective (owner request 2026-10-22): FR-120 to FR-126, AC-46 to AC-61, T-117 to T-128 (ADR-012 for running next to 1.0).

BR identifiers follow BRD section 9. Test IDs (T-xxx) are from the Test Plan and E-numbers from the Evaluation Plan. O6's AC cell is the benchmark ADR target, which is set on Day 1. Coverage check: every FR above FR-92 appears in at least one story; FR-65 and FR-32 sit in Could stories.
