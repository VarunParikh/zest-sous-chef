# Product Research: Zest AI Sous-Chef

Status: DRAFT v0.1 (awaiting owner approval) · Date: 2026-10-16
Basis: the owner-supplied market research (`market-research-source.md`), read against the product vision, Settings Panel and user journeys. No new web research was done for this version. The supplied file itself has no source links. The owner later supplied six URLs (Blinkit x2, JioMart, Shopvora x2, Zepto), which we checked on 2026-10-17: the JioMart and Shopvora pages loaded and support some claims; the Blinkit and Zepto pages did not load in our session. See section 9 and the claims ledger in the Risk Register. Claims without a verified source stay labelled "as supplied" and must not be stated as fact in an interview.

## 1. Question and recommendation
**Question:** Is a conversational, lever-driven recipe-to-cart assistant worth building, and where does it fit among Indian quick-commerce players?

**Recommendation: Go (for the prototype).** The supplied research shows recipe-to-cart is a live strategic feature, and one player (Instamart) already does chat-based carts. Zest's defensible angle is not "chat that fills a cart" but **inspectable recommendation levers, code-enforced dietary and faith guardrails, and pantry-aware carts from photos and videos**.

## 2. What the supplied research says (as supplied, unverified)

| Player | Recipe flow | Technology | Recommendations |
|---|---|---|---|
| **Blinkit** | Recipe pages with an ADD button per ingredient and delivery estimate | Generative AI with Microsoft to mass-produce localised recipes | Grouped by moods and times of day; brand stores weave sponsor products into recipes |
| **Zepto** | "Explore All Recipes" hub by meal type and diet, with prep times | Native curated catalogue; backend ingredient bundles | Seasonal and festive collections |
| **Swiggy Instamart** | Chat prompts through an MCP server that lets AI assistants search, cart and check out | Conversational AI with the Model Context Protocol | Constraints in the prompt (budget, keto, vegan) drive the exact SKUs |
| **JioMart** | No prominent recipe-to-cart; recipe mixes through search | Predictive search | Behavioural history shapes homepage and cart suggestions |

Trends in the file: AI is the differentiator; recipe-to-cart is becoming a retail-media (brand sponsorship) channel; the market splits into static or catalogue-based (JioMart, Zepto) and dynamic or content-driven (Blinkit, Instamart).

## 3. Facts, assumptions, unknowns

| Type | Item |
|---|---|
| Fact (supplied) | Four players, four different approaches (table above) |
| Fact (project) | Zest targets a JioMart-like store with mock data only |
| Assumption | The supplied claims are accurate and current as of October 2026 |
| Assumption | A mock-data prototype demonstrates the idea convincingly enough for the interview |
| Unknown | Real conversion or basket-size uplift from recipe-to-cart (the file gives no numbers) |
| Unknown | Whether Instamart's chat flow offers inspectable controls like Zest's levers |
| Unknown | Source quality for each claim (no links in the supplied file) |

## 4. Where Zest sits

| Capability | Blinkit | Zepto | Instamart | JioMart | **Zest** |
|---|---|---|---|---|---|
| Recipe to cart | Page-based | Hub-based | Chat | Search only | Chat, link, photo, mood |
| Natural-language constraints | No | Filters | Yes | No | Yes, plus levers |
| Dietary and faith guardrails as hard filters | Filters (as supplied) | Veg / Egg / Non-veg tags | Prompt-based | Not stated | **Code-enforced, tested** |
| Pantry-aware ("only what's missing") | Not stated | Not stated | Not stated | Not stated | **Photo and text delta** |
| Video recipe to cart | Not stated | Not stated | Not stated | Not stated | **YouTube transcript** |
| Visible recommendation controls | No | No | No | No | **Lever panel with score breakdown** |
| Behavioural history | Not stated | Not stated | Not stated | Yes | Simulated by sliders |
| Sponsored placement | Yes (brand stores) | Not stated | Not stated | Not stated | None; disclosure principle if ever added |

"Not stated" means the supplied research is silent, not that the feature is absent.

## 5. Alignment with the assignment
| Research finding | Zest response | Journeys |
|---|---|---|
| Contextual and mood-based curation (Blinkit) | Mood and intent entry method (B3) | UJ6 |
| Festive and seasonal picks (Zepto) | Trend levers; Shravan faith option | UJ11, Settings Panel section 6 |
| Constraint-driven chat carts (Instamart) | Persona and specialised-diet masks, price cap | UJ7, UJ21; UJ17 (Could) |
| Behavioural recommendations (JioMart) | History sliders and weights | UJ11, UJ12 |
| Brand-sponsored default SKUs | Out of scope; the research warns of ranking bias | Risk R-Sponsor |
| Chat-based cart editing | Conversational cart edits | UJ5 |

## 6. Implications for the recommendation engine
**Weight handling (answers the owner's question on weights).** Best practice for weighted hybrid recommenders is to normalise each component score to a common range and combine them as a convex combination (weights non-negative and summing to 1), so the final score stays on a fixed scale and each weight reads as a relative share. See Burke (2002) [R7] on weighted hybrids.

Decision for the PRD:
1. Each component score (culinary pairing, history, trend, persona and gourmet) is normalised to 0 to 1 per candidate set.
2. The four weight sliders stay independent in the UI. The engine uses **effective weights** `ŵ = w / Σw`.
3. If all four are 0, the engine restores the defaults and the UI shows a note.
4. `S_final = M_elig × Σ(ŵ_k × s_k)`, where `M_elig` is the 0 or 1 guardrail mask.
5. The UI shows the effective percentages beside the sliders and a per-item score breakdown (as `DESIGN.md` specifies).
6. The price cap, stock filter and all dropdown guardrails are **filters or caps**, not weights; they are never renormalised.

**Why not just clamp:** clamping hides the relative effect of a slider once several are high, which undermines the product's core promise that levers visibly change recommendations.

## 7. Risks surfaced by the research
| ID | Risk | Note |
|---|---|---|
| R-Claims | Market claims have no sources | Source or soften before the interview |
| R-Sponsor | Retail-media pressure could bias ranking | Zest ranks on levers only; disclose any future sponsored slot |
| R-Incumbent | Instamart already offers chat carts | Differentiate on levers, guardrails and pantry awareness |
| R-Static | JioMart has no recipe flow, so there is no real reference for the "linked to JioMart" idea | We simulate a JioMart-style store with mock data (C5) |

## 8. Next research steps (optional)
1. Source each competitor claim with a public link or screenshot.
2. Check whether the Instamart MCP flow exposes any user-adjustable controls.
3. Gather any published figures on recipe-to-cart conversion.

## 9. Sources
- Owner-supplied market research: `docs/epics/zest/discovery/market-research-source.md` (no links in the original).
- Owner-supplied sources (accessed 2026-10-17):
  - Jio. *JioMart app.* https://www.jio.com/apps/jiomart/ (loaded; supports purchase-history recommendations; describes a shopping-list tool, no recipe feature)
  - Shopvora. *Recipes.* https://shopvora.in/recipes and https://shopvora.in/recipes?region=North+India (loaded; third-party recipe-to-cart tool powered by Swiggy Instamart, with diet, budget-per-plate, region and meal-time filters)
  - Blinkit. *Breakfast boosters recipe.* https://blinkit.com/recipe/54319 and *Almond milk chia pudding recipe.* https://blinkit.com/recipe/51801 (did not load for us; unverified)
  - Zepto. *Hidden Chefs kadai chicken masala kit.* https://www.zepto.com/pn/hidden-chefs-kadai-chicken-masala-kit-recipe-kit/pvid/c0b61844-96f9-448b-82c4-cefd79e56bab (loaded empty; unverified)
- **New market observation:** Shopvora shows a "budget per plate" filter and a regional filter on top of Instamart. That supports Zest's cost-aware persona (P10) and suggests the cart budget gap noted in the Personas document is worth revisiting.
- [R7] Burke, R. (2002). *Hybrid recommender systems: survey and experiments.* User Modeling and User-Adapted Interaction 12(4), 331–370 (cited from knowledge; verify before submission).
- Project documents: `product-vision.md`, `RecommendationSettingsPanel.md`, `UserJourneys.md`.
