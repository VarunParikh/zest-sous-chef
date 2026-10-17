# Test Cases (Given / When / Then)

Status: **Draft (amended 2026-10-17): awaiting owner re-approval**; content mirrors Test Plan v0.2 (v0.1 was approved by the owner 2026-10-17; T-047 to T-049 are new) · Date: 2026-10-17
**Status of every test: NOT RUN.** No code exists. This file expresses each test in the plan's catalogue (`test-plan.md` section 4) as Given / When / Then without changing its ID, coverage or priority. If this file and `test-plan.md` ever disagree on what a test proves, log it in `docs/core/open-conflicts.md`. Tests assert structure (message IDs, slot values, SKU IDs, quantities, totals), not wording (NFR-11). "Fake" doubles are those in test-plan section 3.

## 4.1 Session and levers
| ID | Given | When | Then | Covers | Pri |
|---|---|---|---|---|---|
| T-001 | A session started with lever snapshot S and a recorded response R to a fixed prompt | The levers are edited in the panel and the same prompt is sent in the same session | The recommendations equal R (the snapshot is used) | FR-02, AC-01 | P0 |
| T-002 | A session whose snapshot differs from the current lever values | The turn response is built | `levers_changed_since_snapshot` is true and the banner flag is set; it is false when the values match | FR-03 | P0 |
| T-003 | Levers changed after a session ended | A new session is created | The new snapshot holds the new lever values | FR-01 | P0 |
| T-004 | Weights 80/80/40/0, then weights 0/0/0/0 | The engine resolves the weights | Shares are 0.4/0.4/0.2/0 and sum to 1; all zeros return the defaults and set the notice flag | FR-08, AC-03 | P0 |
| T-005 | Lever payloads with an out-of-range slider and a price cap of 79 | A session is created | The request is rejected with `INVALID_LEVERS` and no session exists | FR-06 | P0 |
| T-006 | Persona Jain faith with Non-Veg diet | The eligibility mask is built | The masks are intersected and a conflict warning is returned | FR-09, AC-25 | P1 |
| T-007 | A cart with items | Clear chat is requested, first cancelled, then confirmed | Cancel changes nothing; confirm empties the cart; the levers are untouched in both cases | FR-04, AC-18 | P0 |
| T-008 | Changed levers, a chat history and a snapshot | Reset levers is pressed | The lever values return to defaults; chat and snapshot are untouched | FR-05, AC-19 | P1 |

## 4.2 Eligibility and guardrails
| ID | Given | When | Then | Covers | Pri |
|---|---|---|---|---|---|
| T-010 | Each of the 11 personas, all variants and all dishes, and rules computed independently from tags | The eligibility mask is applied (parametrised) | No ineligible item passes for any persona | FR-60, 90, O2 | P0 |
| T-011 | Persona Jain and a request for Garlic Bread | The dish is resolved and carted | No `onion_garlic` or `root_veg` variant is eligible, a compliant alternative is offered, and no garlic is in the cart | FR-90, AC-04 | P0 |
| T-012 | Persona Pure Veg and a chicken-video fixture | The video flow runs | The mismatch is flagged and no meat, fish or egg item enters the cart | AC-05 | P0 |
| T-013 | Persona Halal and meat variants including some tagged `not_halal`, plus alcohol | Eligibility is evaluated | `not_halal` meat and alcohol are excluded | FR-60 | P0 |
| T-014 | Persona Shravan and variants tagged `non_satvik` | Eligibility is evaluated | All `non_satvik` variants are excluded | FR-60 | P1 |
| T-015 | Persona Keto and staples above the carb limit | Eligibility is evaluated | Those staples are filtered and flagged | FR-60, AC-06 | P1 |
| T-016 | Personas Vegan, Gluten-Free and Low-GI | Eligibility is evaluated | Each mask excludes exactly the items its rule forbids | FR-60 | P1 |
| T-017 | An item with zero stock | The stock filter is on, then off | On: the item is removed. Off: it is kept and flagged, and Buy Now is blocked | FR-83, F-10 | P0 |
| T-018 | A price cap lever and a cart with dishes and add-ons | Suggestions are ranked | The cap applies to add-ons only, not to dish choices | FR-60 | P1 |
| T-019 | A variant containing gelatin or parmesan in its ingredient list | A Pure Veg mask is applied | It is excluded through the ingredient list, even if its tags look vegetarian | FR-91 | P1 |
| T-020 | A test dataset with one deliberately mis-tagged variant | Validator V3 runs | The build fails (canary proves the validator works) | G4, S-08 | P0 |
| T-021 | A vector candidate that breaks the active persona | Retrieval then guardrails run | The candidate is removed and `guardrail_filtered` is traced | FR-112, AC-37 | P0 |
| T-022 | An active persona | The user asks the bot to change persona in chat | The persona is unchanged and the reply points to the panel | FR-90 | P1 |

## 4.3 Scoring and variants
| ID | Given | When | Then | Covers | Pri |
|---|---|---|---|---|---|
| T-030 | A candidate pool with component values | Components are normalised | `s_p` is rank-based, the others are min-max, and all-equal inputs give 0.5 | App. A | P0 |
| T-031 | A scored candidate with a breakdown | The score is computed | `S_final` equals the weighted sum and the breakdown components sum to the score | FR-61, AC-20 | P0 |
| T-032 | Candidates with tied scores | The ranking runs repeatedly | Ties break by `s_p`, then ID, and repeated runs are identical | FR-66 | P0 |
| T-033 | A fixed pool and one weight raised at a time, per component | The ranking is recomputed | The pool reorders in the expected direction for that component | FR-02, US-17 | P0 |
| T-034 | A recommendation request | The pool is built and displayed | The pool has at least 15 candidates and exactly 3 are displayed | FR-111, AC-36 | P0 |
| T-035 | An ingredient with at least 4 variants | The organic slider and the gourmet slider (0 versus 1) change | The chosen variant changes with each, via the value term | FR-113, AC-38, 42 | P0 |
| T-036 | A request naming an attribute ("skimmed milk") | Variants are selected under any slider settings | Only variants with that attribute are eligible | AC-39 | P0 |
| T-037 | A frozen `Context` from config | Trend scores are computed twice | The trend effects are identical | FR-67 | P1 |
| T-038 | A probable-gender setting | `s_g` is computed | The boost is capped at 10% of `s_g` and nothing is filtered | FR-07 | P1 |
| T-039 | An add-on rejected by the user | Later suggestions are ranked in the same session | That category's weight is lowered for this session only and decays | FR-65 | P1 (Could) |

## 4.4 Retrieval
| ID | Given | When | Then | Covers | Pri |
|---|---|---|---|---|---|
| T-040 | Two rankings with a hand-computed expected result | Reciprocal rank fusion runs | The merged order and scores match the hand calculation | FR-110 | P0 |
| T-041 | The lexical retriever and synonym table | "kothmir", "kandha" and "batata" are searched | They resolve to coriander leaves, onion and potato | AC-17 | P0 |
| T-042 | The vector store disabled | A search runs | Retrieval falls back to lexical and `fallback_used` is traced | FR-117, AC-40 | P0 |
| T-043 | An ambiguous term ("methi") with top two candidates closer than the margin | The term is resolved | A clarifying question is asked and nothing is carted | FR-13 | P0 |
| T-044 | An existing index | The catalogue hash or the embedder changes | The index is rebuilt | NFR-12 | P1 |
| T-045 | The embedding text generator | Embedding text is produced for variants | No price or stock token appears | V11 | P1 |
| T-046 | A completed retrieval | The inspector payload is requested | It lists lexical rank, vector rank, fused rank, eligibility and final score | FR-115, AC-41 | P1 |
| T-047 | A curated list and a vector list for one cart dish, with a hand-computed expected result (curated weight 2, vector weight 1, k = 60) | Weighted reciprocal rank fusion runs for add-ons | The merged order and scores match the hand calculation; equal scores break by curated strength, then ID; a dish in one list scores from that list alone | FR-118 | P0 |
| T-048 | A cart dish whose vector neighbours include a main course and a dish that breaks the active persona, plus eligible side, beverage and dessert neighbours | Add-on candidates are built, fused and filtered | Only side, beverage and dessert vector candidates enter the fusion; the persona-breaking candidate is removed after fusion and `guardrail_filtered` is traced | FR-118, 119, AC-44 | P0 |
| T-049 | A cart dish with no curated pair, then the same dish with the vector store disabled | Add-on suggestions are requested in each case | First, at least one eligible companion-course add-on is offered and none is added without a tap; then the curated list alone is used (or none, if it has no pair) and `fallback_used` is traced with no error shown | FR-118, 117, AC-43, AC-45 | P0 |

## 4.5 Cart and checkout
| ID | Given | When | Then | Covers | Pri |
|---|---|---|---|---|---|
| T-050 | A need of 200 g paneer twice and available pack sizes | Packs are allocated | The smallest pack set covering the need is chosen (two packs) | FR-71, AC-24 | P0 |
| T-051 | Two dishes sharing butter within one pack | Both are carted | The first line is active and priced, the second is dimmed and unpriced | FR-73, AC-08 | P0 |
| T-052 | The same shared-butter cart | The owning line is removed | Ownership transfers and totals stay correct | AC-08 | P0 |
| T-053 | A cart with dishes and lines | Totals are computed | Each dish total equals the sum of its active lines and the subtotal equals the sum of dishes | FR-72 | P0 |
| T-054 | A cart line | Quantities 0, 1, 9 and 10 are requested | Only 1 to 9 are accepted | FR-74 | P0 |
| T-055 | A cart with lines and dishes | A line, then a dish, is removed | Only the targeted item is removed and totals update | FR-74 | P0 |
| T-056 | An empty cart, then a cart with items | The cart icon state is requested | Empty: disabled with no badge. Items: enabled with the correct count | FR-75, AC-12 | P0 |
| T-057 | A valid cart and an idempotency key | Buy Now is sent twice with the same key | Exactly one order exists and the second call returns the same order | FR-80, AC-13 | P0 |
| T-058 | A cart where an item's stock drops to zero and another's price changed | Checkout is attempted | Checkout is blocked for the stock-out and the price change is shown | FR-83, AC-28 | P0 |
| T-059 | A suggested substitution | It is offered, then accepted | The cart changes only after acceptance | FR-76, AC-33 | P0 |
| T-060 | A cart and the message "do something else" | The message is handled | A replace-or-add question is asked, nothing is cleared before confirmation, and Undo restores the cart | FR-77 | P0 |
| T-061 | A reply that cites prices, including one deliberately wrong | The reply validator runs | Every price equals the catalogue value; the wrong one is corrected | FR-79, AC-14 | P0 |
| T-062 | A mood suggestion carted with two swaps offered | A swap is chosen, then Undo is pressed | Only the suggested dish is replaced, and Undo restores the prior cart | FR-41, AC-30 | P0 |

## 4.6 Guard and injection
| ID | Given | When | Then | Covers | Pri |
|---|---|---|---|---|---|
| T-070 | An off-topic prompt and an injection prompt | Each is sent | The reply is MSG-REDIRECT and the cart is unchanged | FR-10, AC-15 | P0 |
| T-071 | Benign cooking phrases such as "attack the onions" | They are sent | They are not blocked and are routed normally | AC-22 | P0 |
| T-072 | A transcript fixture containing an embedded instruction | The video flow runs | The instruction is ignored and the cart is unchanged | FR-12, AC-21 | P0 |
| T-073 | Hazardous and alcohol requests | They are sent | They are refused | UJ59 | P1 |
| T-074 | A request for allergy assurance | It is sent | The reply is MSG-ALLERGY | FR-15 | P1 |
| T-075 | Messages containing markup and script strings | They are rendered in the UI | They display as inert text and execute nothing | S-06 | P0 (E2E) |

## 4.7 Flow acceptance (fake model)
| ID | Given | When | Then | Covers | Pri |
|---|---|---|---|---|---|
| T-080 | A demo YouTube link with a fixture | The link is sent | Ingredients are extracted, mapped to variants and carted at catalogue prices | AC-07, US-08 | P0 |
| T-081 | Live transcript fetch failing, then both live and fixture failing | The link is sent in each case | First the fixture is used; then the paste prompt is shown | AC-16 | P0 |
| T-082 | A non-YouTube URL, and the same video sent twice | Each is sent | The URL is rejected with no network call; the second send asks before repeating | FR-24, AC-31 | P0 |
| T-083 | A text recipe split across several messages | They are sent, then "new dish" | Ingredients are carted immediately under one open dish, and "new dish" closes it | FR-30, US-11 | P0 |
| T-084 | A dish name the catalogue does not know | It is sent | The bot asks for ingredients or offers the nearest dishes | FR-33, AC-26 | P1 |
| T-085 | A mood message and an eligible dish set | It is sent | The top dish is carted, two swaps are offered and Undo works | FR-40, 41, AC-09 | P0 |
| T-086 | A mood message where no dish is eligible for the persona | It is sent | Nothing is added and the reply says why | FR-42, AC-29 | P0 |
| T-087 | A photo upload | The photo flow runs | Consent is asked first, low-confidence items are confirmed, and only the top dish's missing items are carted | FR-50 to 54, AC-10 | P0 |
| T-088 | Gemini failing or timing out | A photo is submitted | Labelled sample photos are offered | FR-55, AC-11 | P0 |
| T-089 | A wrong-type, an oversize and a spoofed-type upload | Each is uploaded | Each is rejected with the defined error | FR-57, AC-23 | P0 |
| T-090 | The fake model returning invalid JSON | A message is processed | It is retried once and then MSG-REPHRASE is shown | NFR-10 | P0 |
| T-091 | The fake model timing out | A message is processed | The defined fallback is used and a success message is never shown | NFR-02 | P0 |
| T-092 | A cart from one video | A second link with shared ingredients is sent | Shared ingredients are aggregated and the bot asks about staples | FR-23 | P1 |
| T-093 | A message being processed | The input is used and a second message is sent | The input is locked and the second message returns `SESSION_BUSY` | FR-102, AC-27 | P0 |
| T-094 | An action reference from an earlier turn | It is sent after the cart changed | The response is `STALE_ACTION` | API Spec | P1 |

## 4.8 Data, security and privacy
| ID | Given | When | Then | Covers | Pri |
|---|---|---|---|---|---|
| T-100 | The shipped data and a fixed seed | Validators V1 to V14 run and generation runs twice | All validators pass and both outputs are byte-identical | NFR-08, V13 | P0 |
| T-101 | The dish list and the catalogue | Coverage is checked | Every dish ingredient resolves to at least one variant (except the by-design Sushi gaps) and lever-test ingredients have at least 4 variants | V8 | P0 |
| T-102 | A fixture image with GPS metadata | The image is processed | The GPS tag is absent from the processed bytes | FR-51, S-03 | P0 |
| T-103 | An image upload flow | Processing completes or fails | Image bytes are never written to disk or logs | NFR-06, AC-34 | P0 |
| T-104 | Crafted URLs (`file://`, internal IPs, look-alike domains) | Each is submitted | Each is rejected and no fetch is attempted | S-05 | P0 |
| T-105 | `DEMO_CONTROLS` unset | A demo endpoint is called | It returns 404; with `DEMO_CONTROLS=true` it works | S-09 | P1 |
| T-106 | The repository tree and full history | The secret scan runs | It finds nothing | S-01 | P0 |
| T-107 | The `.gitignore` file | It is inspected | It covers `.env`, logs, the Chroma folder and uploads | S-07 | P0 |
| T-108 | Session creation and a request with an unknown ID | IDs are generated and the unknown ID is used | IDs are random and the unknown ID returns 404 | S-12 | P1 |
| T-109 | A processed chat turn with a long message and an image | The trace log is written | It contains truncated text and no images | NFR-06 | P1 |

## 4.9 Interface and accessibility
| ID | Given | When | Then | Covers | Pri |
|---|---|---|---|---|---|
| E2E-001 | The app loaded in a real browser with the fake model | The user loads the page, picks a persona preset, starts a new session, sends the mood message, taps a swap, opens the cart, changes a quantity, presses Buy Now and waits for the collapse | The split screen and greeting show; the cart badge appears; the order message appears and the progress bar runs for 10 s; then the cart is empty and the icon disabled. Also: Tab reaches the cart icon, the cart window traps focus and Escape closes it when not in the order state, and markup renders inert (T-075) | AC-12, 13, 32; FR-81, 100 to 104 | P0 |
| T-110 | The app at widths above and below 1024 px | The window is resized (manual check during rehearsal) | The layout switches responsively below 1024 px | FR-100 | P1 |
