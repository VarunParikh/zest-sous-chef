# Product Strategy: Zest AI Sous-Chef

Status: DRAFT v0.1 (awaiting owner approval) · Date: 2026-10-16

## 1. Purpose
Zest turns a cooking intent (a YouTube recipe, a typed dish or mood, or a photo of ingredients) into a correct, dietary-compliant quick-commerce cart in a few messages. Its defining feature is a transparent recommendation engine whose levers visibly change what the bot suggests.

This is an interview prototype. Its job is to demonstrate product judgement, AI-lifecycle discipline and a working end-to-end system, not to be a production service.

## 2. Problem
Turning "what should I cook?" into a delivered basket today takes many steps: find a recipe, read it, check the pantry, search each item, check diet constraints, and add items one by one. Quick-commerce apps recommend products but don't understand recipes, constraints or the user's pantry.

## 3. Users
| User | Need | How Zest serves them |
|---|---|---|
| **Home cook** (primary) | Fast path from idea or video to the right basket, respecting diet and faith | Chat in text, links or photos; the cart is built and explained |
| **Reviewer / product owner** (secondary, in this prototype) | See and test how recommendation logic changes bot behaviour | Left-hand lever panel, applied at the start of each chat session |

## 4. Value proposition
1. **Any starting point:** link, text, mood or photo.
2. **Only what's missing:** the photo and pantry delta means no duplicate buying.
3. **Safe by construction:** diet, faith and allergy rules are hard filters.
4. **Explainable:** levers and a score breakdown show why an item was suggested.

## 5. Goals and success measures
| Goal | Measure | Target (prototype) |
|---|---|---|
| Levers are causal | For each lever group, a scripted change alters the top suggestions in a test | 100% of lever groups demonstrate an effect |
| Guardrails hold | Ineligible items appearing in cart or suggestions in the guardrail test set | 0 |
| Commerce is grounded | Prices and SKUs in chat that match the catalogue | 100% |
| Journeys work | MVP journey tests passing | 100% of Must, at least 80% of Should |
| Edge cases handled | Edge-case evaluation set, graceful response rate | At least 90% |
| Responsiveness | Text-to-cart time on the demo laptop | Under 15 s typical (to be measured) |

Targets are working assumptions and will be tightened in the Evaluation Plan.

## 6. Scope

### 6.1 Brief-defined capabilities (all in scope)
| ID | Capability |
|---|---|
| B1 | Cart from a YouTube link (transcript analysis) |
| B2 | Cart from a text recipe in one or several messages |
| B3 | Cart from a natural-language mood or intent ("I am feeling indulgent") |
| B4 | Cart from a photo: identify ingredients, suggest recipes, add only the missing items |
| B5 | Cart UI: top-right icon with badge, greyed out when empty, per-dish and per-ingredient edit and remove, Buy Now, mobile-shaped window, order-placed message, 10 s collapse with progress bar |
| B6 | Left-panel levers apply to the **next** chat session; chat clear and engine reset work independently |

### 6.2 User journeys from `UserJourneys.md`
| Tier | Journeys | Rule |
|---|---|---|
| **Must** | UJ1, UJ2, UJ3, UJ6, UJ7, UJ9, UJ10, UJ20, UJ23 | Fully built and tested |
| **Should** | UJ5, UJ8, UJ11, UJ12, UJ21, UJ22, UJ57, UJ60, UJ61 | Built if Must is green |
| **Could** | UJ4, UJ16, UJ17, UJ24, UJ29 (Jain/Veg only) | Only with spare time |
| **Deferred** | All others (including UJ13–15, 18–19, 25–56 except above, 58–59, 62–87) | Documented, not built; reasons in the Known Limitations note |

Notes:
- UJ11 and UJ12 are **suggest-only**, per the Constitution. UJ12 learning from rejection is in-session only, because a browser refresh resets all state.
- "Purchase history" is simulated by the history sliders. There is no real order history.
- UJ19 (opaque photos) and UJ47 (look-alike items) are deferred, but the vision step must report confidence and ask when it is low.

### 6.3 Non-goals
Real JioMart or payment integration · real order tracking · accounts and login · multi-language beyond the Marathi/Hinglish ingredient names in UJ23 · voice input · persistence across refresh · production scale.

## 7. Differentiation and strategic bets
| Bet | Why it matters |
|---|---|
| **Guardrails before ranking** | Trust: a Jain user never sees garlic |
| **Catalogue-grounded AI** | The LLM understands; the catalogue decides prices and SKUs |
| **Levers as a product surface** | Makes the recommendation engine inspectable, a strong interview demonstration |
| **Local-first models** | Zero running cost, data stays on the laptop; trade-off is speed and accuracy |

## 8. Delivery strategy (3 days)
The documents were completed before the build (decision of 2026-10-17), so the three build days now follow `docs/epics/zest/build-plan.md`:
| Day | Focus |
|---|---|
| 1 | Repo scaffold, mock data and validators, recommendation engine, retrieval, decision benchmarks |
| 2 | Sessions, cart, flows (mood first), API, frontend, lever and persona evaluations |
| 3 | End-to-end test, fault injection, latency, evidence report, README, demo script, limitations, rehearsals, publish |
The plan, gates and cut order are in the build plan; this table is a summary.

## 9. Key strategic risks (details in the Risk Register)
1. Local vision and LLM quality or speed on 16 GB RAM.
2. YouTube transcript retrieval is unofficial and fragile (UJ55); fallbacks are defined.
3. Scope is wider than 3 days allow, so the tiering above is the control.
4. Spec conflicts between source documents; tracked in `open-conflicts.md`.

## 10. Decisions recorded
- C4 resolved: lever changes apply from the next chat session, because chat clear and engine reset are independent of the lever panel.
- Brief-defined journeys (B1–B6) are in the MVP.
- Upsells are suggested, never auto-added.
