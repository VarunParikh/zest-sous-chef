# Test Plan: Zest AI Sous-Chef

Status: **APPROVED v0.7 (owner, 2026-10-22, with the Zest 2.0 plan): §4.10 adds T-117 to T-128.** v0.6 was **APPROVED v0.6 (owner, 2026-10-19, with the block 3.3 plan): §9 step 6 and T-105 NOT RUN, demo endpoints cut (C72).** v0.5 was **APPROVED (owner, 2026-10-18, C68): T-100 covers V1 to V17.** v0.4 was **APPROVED (owner re-approved 2026-10-18) (2026-10-18): C37 doc-sync to ADR-003 v3 (local `qwen3-vl:4b-instruct` default, Gemini opt-in, samples for the demo and as fallback). ** v0.3 was APPROVED (owner, 2026-10-18), re-approved after the C15 sync to the ADR-003 Day-1 decision.** v0.2 was APPROVED (owner, 2026-10-17) (v0.1 was approved earlier the same day; v0.2 adds T-047 to T-049 for ADR-004 v2 add-on retrieval) · Date: 2026-10-17 · Source: PRD v0.4 (AC-01 to AC-45), User Stories, Architecture, API Spec, Agent Design, Security and Privacy Note
Owner decision (2026-10-17): **lean test set.** Full coverage of the engine, cart and guardrails; acceptance tests for the Must stories; one Playwright demo-path test. Dependency Pillow approved.
**Status of every test in this plan: NOT RUN.** No code exists. Nothing here is a result.

## 1. Principles
1. **Tests before code per story** (Constitution G4, playbook). A story is done only when its tests pass.
2. **Deterministic by construction.** Unit and acceptance tests never call a real model, Gemini, YouTube or a downloaded embedder. They use fakes, fixtures and seeded data (NFR-08, 11).
3. **Real-model behaviour is measured by evaluations, not asserted by tests.** Model quality is in the Evaluation Plan. A flaky model must not make the build flaky.
4. **Guardrail tests are build-failing and untouchable.** Never weaken or delete one to get green (G4). A canary test proves the validators actually catch a planted bad tag.
5. **Assert structure, not wording:** message IDs, slot values, SKU IDs, quantities, totals (NFR-11).
6. **No coverage number is claimed unless a tool measured it.**

## 2. Levels and tools (lean)
| Level | Scope | Tooling | Runs |
|---|---|---|---|
| Unit | Engine, eligibility, scoring, variant choice, retrieval fusion, pack allocation, cart, guard rules, scaling, validators, EXIF stripping | `pytest` | Every change |
| Contract / API | Endpoints, card schemas, error codes, idempotent checkout, busy and stale handling | `pytest` + FastAPI `TestClient` (needs `httpx`) | Every change |
| Acceptance (Must stories) | End-to-end through the pipeline with fake model and fixtures; asserts the AC table | `pytest` | Every change |
| End-to-end UI | **One** demo-path test in a real browser | Playwright (`pytest-playwright`) with `LLM_PROVIDER=fake` | Before each demo rehearsal |
| Evaluation | Real model, Gemini, real embedder; measured, reported | `eval/` harness (Evaluation Plan) | Day 1 to 3 |
| Manual rehearsal | Live model, live Gemini, live transcript, network-off | Checklist (section 9) | Day 2 evening, Day 3 morning |
New dependencies approved by the owner on 2026-10-17 ("Approve all", build-plan section 4): `pytest`, `httpx`, `pytest-playwright` and Playwright browsers, `coverage`.

## 3. Test doubles and fixtures
| Double | Behaviour |
|---|---|
| `FakeLLM` | Returns canned JSON keyed by a normalised input; can be set to return invalid JSON, time out, or raise (for fallback tests) |
| `FakeVision` | Returns a `DetectionResult` from a fixture; can fail or time out |
| `FakeTranscript` | Returns fixture text, or raises `TranscriptUnavailable` |
| `FakeEmbedder` | Deterministic hash-based vectors so Chroma behaves reproducibly offline |
| Test catalogue | A small seeded catalogue (about 60 variants, 12 dishes plus at least 6 companion-course dishes for the add-on tests (a proposed size), 4 personas) built by the same generator; plus the full 1,000-variant set in a slower marker `-m full_catalogue` |
| Clock and context | Frozen `Context` (time, weather) |
Shared fixtures: `personas.json`, transcript fixtures, sample photos with expected detections, stock scenarios.

## 4. Test catalogue
IDs are stable. Priority P0 = must pass before any demo; P1 = should pass.
**Format:** the tables below are the index (ID, title, coverage, priority). The full Given / When / Then for every test is in `test-cases.md`; both use the same IDs (checked 2026-10-17 at v0.1: 84 IDs, no missing or extra, coverage and priority identical; v0.2 adds T-047 to T-049 to both files, so 87 IDs, to be re-checked).

### 4.1 Session and levers (US-01 to 04)
| ID | Test | Covers | Pri |
|---|---|---|---|
| T-001 | Lever edit after session start does not change that session's output (snapshot) | FR-02, AC-01 | P0 |
| T-002 | Banner flag true when current levers differ from snapshot | FR-03 | P0 |
| T-003 | New session uses the new levers | FR-01 | P0 |
| T-004 | Weights normalise to shares summing to 1; all zeros restore defaults and set notice | FR-08, AC-03 | P0 |
| T-005 | Out-of-range lever values rejected (`INVALID_LEVERS`), including price cap below 80 | FR-06 | P0 |
| T-006 | Contradictory persona (Jain faith, Non-Veg diet) intersects masks and warns | FR-09, AC-25 | P1 |
| T-007 | Clear chat with items needs confirmation; cancel changes nothing; confirm empties cart; levers untouched | FR-04, AC-18 | P0 |
| T-008 | Reset levers returns defaults without touching chat or snapshot | FR-05, AC-19 | P1 |

### 4.2 Eligibility and guardrails (US-28 to 30; the core of the lean set)
| ID | Test | Covers | Pri |
|---|---|---|---|
| T-010 | Parametrised: for each of the 11 personas, over all variants and dishes, no ineligible item passes the mask (property-style check against rules computed independently from tags) | FR-60, 90, O2 | P0 |
| T-011 | Jain: no `onion_garlic` or `root_veg` variant; Garlic Bread request yields a compliant alternative and no garlic in cart | FR-90, AC-04 | P0 |
| T-012 | Pure Veg: no meat, fish or egg; chicken-video flow flags the mismatch | AC-05 | P0 |
| T-013 | Halal: meat variants with `not_halal` excluded; alcohol excluded | FR-60 | P0 |
| T-014 | Shravan: `non_satvik` excluded | FR-60 | P1 |
| T-015 | Keto filters staples above the carb limit and flags them | FR-60, AC-06 | P1 |
| T-016 | Vegan, Gluten-Free, Low-GI masks | FR-60 | P1 |
| T-017 | Stock filter on removes zero-stock items; off keeps them flagged, and Buy Now is blocked | FR-83, F-10 | P0 |
| T-018 | Add-on price cap applies to add-ons only | FR-60 | P1 |
| T-019 | Hidden animal-derived ingredient (gelatin, parmesan) caught through the ingredient list | FR-91 | P1 |
| T-020 | **Canary:** a deliberately mis-tagged variant in a test dataset makes validator V3 fail the build | G4, S-08 | P0 |
| T-021 | Guardrails run after retrieval: a vector candidate that breaks the persona is removed and `guardrail_filtered` is traced | FR-112, AC-37 | P0 |
| T-022 | Bot never changes persona on request | FR-90 | P1 |

### 4.3 Scoring and variants (US-17, 18, 38)
| ID | Test | Covers | Pri |
|---|---|---|---|
| T-030 | Component normalisation: rank-based for `s_p`, min-max for others; all-equal gives 0.5 | App. A | P0 |
| T-031 | `S_final` equals the weighted sum of components; breakdown components sum to the score | FR-61, AC-20 | P0 |
| T-032 | Ties break by `s_p`, then ID; repeated runs identical | FR-66 | P0 |
| T-033 | Raising one weight reorders a fixed pool in the expected direction (monotonic sensitivity, per component) | FR-02, US-17 | P0 |
| T-034 | Candidate pool size is at least 15 and display is 3 | FR-111, AC-36 | P0 |
| T-035 | Variant choice changes with the organic slider, and with gourmet 0 versus 1 (value term) | FR-113, AC-38, 42 | P0 |
| T-036 | User-named attribute ("skimmed milk") restricts eligible variants regardless of sliders | AC-39 | P0 |
| T-037 | Context object from config makes trend effects reproducible | FR-67 | P1 |
| T-038 | Gender boost is capped at 10% of `s_g` and never filters | FR-07 | P1 |
| T-039 | Rejected add-on lowers that category weight for the session only, decaying | FR-65 | P1 (Could) |

### 4.4 Retrieval (US-37, 40)
| ID | Test | Covers | Pri |
|---|---|---|---|
| T-040 | Reciprocal rank fusion merges two rankings per the formula (hand-computed example) | FR-110 | P0 |
| T-041 | Lexical retriever resolves synonyms (kothmir, kandha, batata) | AC-17 | P0 |
| T-042 | With vector store disabled, retrieval falls back to lexical and traces `fallback_used` | FR-117, AC-40 | P0 |
| T-043 | Ambiguous term (methi) triggers a clarifying question when top two differ by less than the margin | FR-13 | P0 |
| T-044 | Index rebuilds when catalogue hash or embedder changes | NFR-12 | P1 |
| T-045 | Embedding text contains no price or stock tokens | V11 | P1 |
| T-046 | Inspector payload lists lexical rank, vector rank, fused rank, eligibility, final | FR-115, AC-41 | P1 |
| T-047 | Weighted RRF for add-ons merges a curated list and a vector list per `Σ w_i / (k + rank_i)` (hand-computed example, curated 2 : vector 1); ties break by curated strength, then ID | FR-118 | P0 |
| T-048 | Course rule keeps only side, beverage and dessert vector candidates, and a vector add-on that breaks the persona is removed after fusion with `guardrail_filtered` traced | FR-118, 119, AC-44 | P0 |
| T-049 | A dish with no curated pair still gets an eligible add-on from the vector list; with the vector store disabled add-ons come from the curated list alone and `fallback_used` is traced | FR-118, 117, AC-43, AC-45 | P0 |

### 4.5 Cart and checkout (US-21 to 27)
| ID | Test | Covers | Pri |
|---|---|---|---|
| T-050 | Smallest pack set covers the need; 200 g paneer needed twice gives two packs | FR-71, AC-24 | P0 |
| T-051 | Shared butter within one pack: first line active and priced, second dimmed and unpriced | FR-73, AC-08 | P0 |
| T-052 | Removing the owning line transfers ownership; totals stay correct | AC-08 | P0 |
| T-053 | Dish total equals sum of active lines; subtotal equals sum of dishes | FR-72 | P0 |
| T-054 | Quantity bounds 1 to 9 | FR-74 | P0 |
| T-055 | Remove line and remove dish | FR-74 | P0 |
| T-056 | Cart icon count and disabled state when empty | FR-75, AC-12 | P0 |
| T-057 | Buy Now creates exactly one order; repeated idempotency key returns the same order | FR-80, AC-13 | P0 |
| T-058 | Checkout blocked when stock drops to zero; price change shown | FR-83, AC-28 | P0 |
| T-059 | Substitution changes the cart only after acceptance | FR-76, AC-33 | P0 |
| T-060 | Replace or add question on ambiguous "do something else"; nothing cleared before confirmation; Undo works | FR-77 | P0 |
| T-061 | Every price in a reply equals the catalogue value; a mismatching value is corrected | FR-79, AC-14 | P0 |
| T-062 | Swap replaces only the suggestion's dish; Undo restores prior cart | FR-41, AC-30 | P0 |

### 4.6 Guard and injection (US-05)
| ID | Test | Covers | Pri |
|---|---|---|---|
| T-070 | Off-topic and injection phrases get MSG-REDIRECT and no cart change | FR-10, AC-15 | P0 |
| T-071 | "Attack the onions" and other benign cooking phrases pass | AC-22 | P0 |
| T-072 | Instruction inside a transcript fixture is ignored; cart unchanged | FR-12, AC-21 | P0 |
| T-073 | Hazardous and alcohol requests refused | UJ59 | P1 |
| T-074 | Allergy assurance request gets MSG-ALLERGY | FR-15 | P1 |
| T-075 | Markup and script strings in messages render inert in the UI | S-06 | P0 (E2E) |

### 4.7 Flow acceptance tests (fake model; Must stories)
| ID | Test | Covers | Pri |
|---|---|---|---|
| T-080 | YouTube demo link: ingredients extracted, mapped, carted at catalogue prices | AC-07, US-08 | P0 |
| T-081 | Transcript chain: live fails, fixture used; both fail, paste prompt | AC-16 | P0 |
| T-082 | Non-YouTube URL rejected without any network call; same video twice asks first | FR-24, AC-31 | P0 |
| T-083 | Text recipe over several messages carts immediately under one open dish; "new dish" closes it | FR-30, US-11 | P0 |
| T-084 | Unknown dish prompts for ingredients or offers nearest dishes | FR-33, AC-26 | P1 |
| T-085 | Mood message adds the top dish, offers two swaps, Undo | FR-40, 41, AC-09 | P0 |
| T-086 | Mood with no eligible dish adds nothing and says why | FR-42, AC-29 | P0 |
| T-087 | Photo flow: consent first, low-confidence confirmation, top dish's missing items only | FR-50 to 54, AC-10 | P0 |
| T-088 | The local vision model (default) or the opt-in Gemini failing or timing out offers labelled sample photos | FR-55, AC-11 | P0 |
| T-089 | Wrong type, oversize and spoofed upload rejected | FR-57, AC-23 | P0 |
| T-090 | Invalid model JSON retried once, then MSG-REPHRASE | NFR-10 | P0 |
| T-091 | Model timeout takes the defined fallback, never a success message | NFR-02 | P0 |
| T-092 | Second link aggregates shared ingredients and asks about staples | FR-23 | P1 |
| T-093 | Input locked while processing; second message returns `SESSION_BUSY` | FR-102, AC-27 | P0 |
| T-094 | Stale action reference returns `STALE_ACTION` | API Spec | P1 |

### 4.8 Data, security and privacy
| ID | Test | Covers | Pri |
|---|---|---|---|
| T-100 | Validators V1 to V17 pass on the shipped data and generation is byte-identical for one seed | NFR-08, V13 | P0 |
| T-101 | Every dish ingredient resolves to at least one variant; lever-test ingredients have at least 4 | V8 | P0 |
| T-102 | EXIF stripped (GPS tag absent after processing) using a fixture image with metadata | FR-51, S-03 | P0 |
| T-103 | Image bytes never written to disk or logs | NFR-06, AC-34 | P0 |
| T-104 | Crafted URLs (file://, internal IPs, look-alike domains) rejected with no fetch | S-05 | P0 |
| T-105 | Demo endpoints return 404 unless `DEMO_CONTROLS=true` (NOT RUN: demo endpoints cut, C72) | S-09 | P1 |
| T-106 | Repo secret scan finds nothing in tree and history | S-01 | P0 |
| T-107 | `.gitignore` covers `.env`, logs, Chroma folder, uploads | S-07 | P0 |
| T-108 | Session IDs are random and unknown IDs return 404 | S-12 | P1 |
| T-109 | Trace log contains truncated text and no images | NFR-06 | P1 |
| T-111 | Launcher platform check rejects Intel and macOS older than 14 with a reason, and warns below 16 GB of RAM (US-41, ADR-011) | NFR-08 | P1 |
| T-112 | Launcher model plan: reuse a running Ollama on 11434 only when it serves all three configured models; otherwise the private server on 11435; lists exactly the missing models | NFR-08 | P1 |
| T-113 | Launcher seeds the runtime folder: copies the bundled index on first launch and on a new app version, never overwrites the same version, and points `CHROMA_PATH` and `TRACE_PATH` outside the bundle | NFR-08, S-07 | P1 |
| T-114 | Packaged server: the built frontend is served at `/`, Zest's API routes are unchanged and take precedence, the setup page reports pull progress, and the bundled `.env` carries no secret | NFR-08, S-01 | P1 |
| T-115 | Manual: open the DMG as a download and reach a carted dish with no terminal step. **PASS 2026-10-22** on the owner's Mac: Gatekeeper Open Anyway, models downloaded from empty, photo analysis ran. Caveat: the owner's own account, not a fresh user or second Mac | US-41 | P1 |

### 4.9 Interface and accessibility (one Playwright test, plus unit-level component checks)
**E2E-001 demo path** (fake model, deterministic): load page and see split screen and greeting; choose a persona preset and start a new session; send the mood message; see the cart badge; tap a swap; open the cart; change a quantity; press Buy Now; see the order message; wait for the 10 second collapse and the progress bar; cart empty and icon disabled. The test also checks: Tab order reaches the cart icon; cart window traps focus and Escape closes it when not in the order state (FR-103); inert markup (T-075).
Component-level checks (React Testing Library, only if the dependency is approved): the lever banner, weight percentage labels, disabled empty cart icon.
| ID | Test | Covers | Pri |
|---|---|---|---|
| E2E-001 | As above | AC-12, 13, 32; FR-81, 100 to 104 | P0 |
| T-110 | Responsive switch below 1024 px (manual check, part of rehearsal) | FR-100 | P1 |
| T-116 | The inspector fills after a named-dish turn (add-on pool only, with a note that no dish pool was ranked), and the empty state says which requests fill it (`tests/e2e/test_inspector.py`) | FR-115, FR-119 | P1 |

### 4.10 Zest 2.0 onboarding and side by side (US-42 to US-47; ADR-012)
E2E tests start with the tour marked as seen (`tests/e2e/conftest.py`), except T-126.
| ID | Test | Covers | Pri |
|---|---|---|---|
| T-117 | E2E: after a persona change, Apply and rerun starts a new session, resends the request and shows Before/Now | FR-120, AC-46, AC-49 | P1 |
| T-118 | E2E: Apply and rerun with items in the cart asks first; Cancel keeps the cart and session | FR-120, AC-47 | P0 |
| T-119 | Unit: every persona preset gets a summary and tag generated from its levers; Jain, vegan and halal wording | FR-121, AC-50 | P1 |
| T-120 | E2E: a persona card selects exactly its preset; Apply and rerun gives a suggestion for that persona | FR-121, AC-51 | P1 |
| T-121 | E2E: every lever in the panel has a tooltip and a Rule or Preference tag; Rule tooltips say "removed" or "never" | FR-122, AC-52, AC-53 | P1 |
| T-122 | Unit: help phrases route to `help`; "help me make paneer butter masala" routes to `named_dish`; long messages are not help | FR-123, AC-54 | P1 |
| T-123 | Acceptance: a help turn returns MSG-HELP with the help card and makes no intent, extraction or reason model call | FR-123, AC-54, AC-55 | P1 |
| T-124 | E2E: "what can I say?" shows the help card and an example produces a cart; the YouTube and Text recipe chips send on one tap | FR-123, FR-124, AC-55, AC-57 | P1 |
| T-125 | Unit: the setup page has five slides, the privacy slide names YouTube and Gemini, a reduced-motion rule exists, and the page loads nothing from the network | FR-125, AC-58, AC-59 | P2 |
| T-126 | E2E: the tour shows on a first visit, Skip hides it after reload, the top-right help icon restarts it, and step 1 waits for a starter | FR-126, AC-56, AC-60, AC-61 | P1 |
| T-127 | Unit: the Mac app's edition constants match `Info.plist`; 2.0 never uses 1.0's data folder or private Ollama port | ADR-012 | P1 |
| T-128 | Manual: Zest 1.0 and Zest 2.0 run at the same time; quitting one leaves the other running; no second model download. **PASS 2026-10-23** on the owner's Mac with the `2.0.0-dev` build: 1.0 on 8000 and 2.0 on 8100 at once, two Dock apps, shared Ollama on 11434; quitting 2.0 left 1.0 answering; 2.0's private Ollama on 11436 read 1.0's model folder with no download | ADR-012 | P1 |

## 5. Acceptance criteria to test map
| AC | Test(s) | AC | Test(s) |
|---|---|---|---|
| AC-01 | T-001 | AC-22 | T-071 |
| AC-02 | Evaluation E6 (not a unit test) | AC-23 | T-089 |
| AC-03 | T-004 | AC-24 | T-050 |
| AC-04 | T-011 | AC-25 | T-006 |
| AC-05 | T-012 | AC-26 | T-084 |
| AC-06 | T-015 | AC-27 | T-093 |
| AC-07 | T-080 | AC-28 | T-058 |
| AC-08 | T-051, 052 | AC-29 | T-086 |
| AC-09 | T-085 | AC-30 | T-062 |
| AC-10 | T-087 | AC-31 | T-082 |
| AC-11 | T-088 | AC-32 | E2E-001 |
| AC-12 | T-056, E2E-001 | AC-33 | T-059 |
| AC-13 | T-057, E2E-001 | AC-34 | T-103, T-109 |
| AC-14 | T-061 | AC-35 | Evaluation E5 (needs a real embedder) |
| AC-15 | T-070 | AC-36 | T-034, E6 |
| AC-16 | T-081 | AC-37 | T-021 |
| AC-17 | T-041 | AC-38 | T-035 |
| AC-18 | T-007 | AC-39 | T-036 |
| AC-19 | T-008 | AC-40 | T-042 |
| AC-20 | T-031 | AC-41 | T-046 |
| AC-21 | T-072 | AC-42 | T-035 |
| AC-43 | T-049 | AC-44 | T-048 |
| AC-45 | T-049 | | |

## 6. What the lean set deliberately does not cover
Full browser tests for every journey; cross-browser testing; visual regression; load or stress testing beyond the 5,000-variant retrieval timing; real-model accuracy as an assertion; accessibility audit with assistive technology (only keyboard and focus checks). These are disclosed gaps, not omissions to hide.

## 7. Commands and recording
| Command | Runs | Output |
|---|---|---|
| `make test` | Unit, contract, acceptance (fakes) | `verify/test-results/latest.xml` |
| `make test-full` | Includes the 1,000-variant catalogue marker | same |
| `make test-e2e` | E2E-001 with the fake model | trace and screenshot on failure |
| `make coverage` | Branch coverage for `engine`, `cart`, `guard` | measured report (target set below) |
| `make eval` | Evaluation Plan | `eval/results/*.json` and the report |
Result statuses: PASS, FAIL, BLOCKED, NOT RUN. A skipped or disabled test is a defect. Coverage target for `engine`, `cart` and `guard`: at least 90% branch coverage. This is a target, not a result.

## 8. Entry and exit criteria
| Gate | Criterion |
|---|---|
| Story done | Its tests exist and pass; docs updated; CHANGELOG entry (CLAUDE.md definition of done) |
| Day 1 exit | Data validators V1 to V14 pass; T-010, T-020, T-040 to T-042, T-047 to T-049 pass; benchmarks run |
| Day 2 exit | All P0 in sections 4.1 to 4.8 pass |
| Demo-ready | E2E-001 passes; manual rehearsal checklist done twice; secret scan clean; release blockers in the Security Note closed |

## 9. Manual rehearsal checklist (live dependencies)
1. Warm-up script run; health page shows model loaded, vision provider status, fixtures present, index ready.
2. YouTube demo link live, then with network blocked (fixture path).
3. Photo: a sample photo (the demo path); a live upload to the local `qwen3-vl:4b-instruct` (may take up to 60 s); if the opt-in is enabled, a Gemini upload with the consent notice; and the provider stopped (sample photos offered).
4. Mood message under three personas (Default, Jain, Keto): different results visible.
5. Lever change, Clear chat, same prompt: different results; inspector shows why.
6. Stock-out scenario via demo controls: NOT RUN, because demo endpoints 14 and 15 were cut with UJ22 (C72). Substitution is covered by T-058 and T-059.
7. Buy Now; 10 second collapse; refresh resets everything.
8. Responsive width check at 1024 px and narrower.

## 10. Risks to the test strategy
| Risk | Mitigation |
|---|---|
| Fakes hide real-model failures | Evaluations E1 to E4, E9, E10 and the manual rehearsal use the real stack |
| Test catalogue differs from the shipped one | Generator is shared; `-m full_catalogue` run before release |
| Time pressure tempts skipping tests | P0 list is the minimum; cut order protects P0 |
| Playwright setup friction on macOS | Single test; setup in the README; fall back to a scripted manual run if blocked |

## 11. Sources
| Source | Used for | Link |
|---|---|---|
| pytest documentation | Test framework | https://docs.pytest.org/ |
| FastAPI testing guide | TestClient | https://fastapi.tiangolo.com/tutorial/testing/ |
| Playwright for Python | E2E | https://playwright.dev/python/ |
| Coverage.py documentation | Measured coverage | https://coverage.readthedocs.io/ |
| OWASP Top 10 for LLM Applications | Security test selection | https://owasp.org/www-project-top-10-for-large-language-model-applications/ |
