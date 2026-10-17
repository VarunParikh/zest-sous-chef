# Product Platforms: Zest AI Sous-Chef

Status: APPROVED v0.1 (owner, 2026-10-17) · Date: 2026-10-16
Model names and limits change quickly. Everything model-specific is configuration (`.env`), never hard-coded. Choices here are provisional until ratified in ADR-001 to ADR-004.

## 1. Platform map

| Layer | Choice | Role | Why | Alternatives considered | Cost |
|---|---|---|---|---|---|
| Backend | **Python 3.12 + FastAPI** | Chat orchestration, recommendation engine, catalogue and cart services | Best local-AI ecosystem; typed schemas; simple to test with `pytest` | Node/TypeScript | Free |
| Frontend | **React + Vite + Tailwind** (design tokens from `DESIGN.md`) | Split screen, chat, cart window | Fast to build; maps cleanly to the design spec | Plain HTML/JS, Next.js | Free |
| Text LLM (default) | **Local model via Ollama** (small instruction-tuned model, to be benchmarked Day 1) | Intent, recipe and ingredient extraction, dish suggestions, replies | Free, private, offline | Cloud LLM | Free |
| Vision (default) | **Gemini API free tier** (a Flash or Flash-Lite model that accepts images) | Identify ingredients in photos | Better accuracy than small local vision models on 16 GB RAM | Local vision model through Ollama | Free tier |
| Vision (fallback) | **Bundled default sample photos** with pre-computed results | Keeps the photo flow demonstrable if Gemini is unavailable | Owner decision, 2026-10-17 | Local vision model (dropped) | Free |
| Guard / classifier | **Rules + small local classifier** (Llama Guard is a candidate, to be verified in ADR-003) | Off-topic, injection and hazard screening (UJ9, UJ57, UJ59) | Guardrails must not depend on the main model's good behaviour | Prompt-only guard | Free |
| Transcripts | **`youtube-transcript-api`** + **pre-saved fixtures** + paste-transcript fallback | YouTube recipes (UJ2, UJ20) | See section 4 | Official YouTube Data API (captions need owner auth) | Free |
| Catalogue and stock | **Mock catalogue service** (JSON/SQLite in `mock-data/`) | SKUs, prices, pack sizes, stock, dark-store flags | Brief requires mock data; scriptable stock-outs for UJ10 and UJ22 | Real platform (not available) | Free |
| Retrieval | **Hybrid: lexical plus synonym table and embedded Chroma vector store** (local ONNX embedder by default; an Ollama embedder is an option to benchmark) merged by reciprocal rank fusion | Ingredient-to-SKU and mood-to-dish candidate pools (IDs only) | Owner decision 2026-10-17; handles mood language and near-variant SKUs; no separate service | Lexical only; networked vector database | Free |
| Recommendation engine | **In-process Python module** | Eligibility filter then weighted score from the lever panel | Core of the product; fully unit-testable | External service | Free |
| State | **In-memory per session** | Cart, chat, levers | `DESIGN.md`: refresh resets everything | Database | Free |
| Testing | `pytest`, Playwright (UI), a scripted evaluation harness | Tests and evaluation | See Test and Evaluation Plans | None | Free |
| Source control | **Git + public GitHub repo** | Delivery | Brief requires GitHub | None | Free |
| Dev tooling | **Claude Code**, VS Code | Build | Brief | None | Free plan limits apply |

## 2. Model routing
A single provider interface with two implementations, chosen by `.env`:
- `LLM_PROVIDER=ollama` (default) for text.
- `VISION_PROVIDER=gemini`. If the Gemini call fails, times out or is rate-limited, the app offers the bundled default sample photos with pre-computed results, clearly labelled as samples (owner decision, 2026-10-17). A local vision model is no longer in the fallback chain.
- No cloud fallback for text prompts (owner decision, 2026-10-17): text runs on the local model only.
- Every LLM call returns schema-validated JSON. One retry, then fallback (Constitution G5).

## 3. Privacy implication of the Gemini free tier (important)
Google's pricing page lists free-tier content as **used to improve its products**. That conflicted with Constitution P9 (photos processed locally). **Resolved by the owner on 2026-10-16 (conflict C8):** Gemini is used with user-uploaded photos, and P9 was amended with a pre-upload notice, EXIF stripping, no storage, a warning to testers, and a labelled sample-photo fallback (ADR-003). The local-vision option was dropped.

## 4. YouTube transcripts
- `youtube-transcript-api` is unofficial. Its own documentation warns that YouTube blocks many cloud-provider IPs and can block self-hosted servers that make too many requests. Running on your own laptop at low volume is the best case, but it can still fail.
- Mitigation, in order: live fetch → bundled fixture for the demo videos → title and description fallback (UJ20) → user pastes the transcript or recipe text.
- Demo reliability rule: the demo script uses 3 to 4 videos that also exist as fixtures.
- Legal and terms-of-service risk is recorded in the Risk Register (UJ55).

## 5. Hardware budget (MacBook Air M5, 16 GB)
- Small local models only. Run one model at a time. Close heavy apps during the demo.
- Benchmark on Day 1: time to first token, tokens per second, and extraction accuracy on 10 sample recipes. The result drives ADR-001.
- Gemini calls offload vision, so no local vision model needs to be loaded at the same time as the text model.
- The embedded vector store and its small embedder run inside the Python process alongside the Ollama text model. Their memory and index build time are not yet measured; the Day-1 benchmark records them (risk R23).

## 6. Mock data (owned by us)
| Dataset | Content | Used by |
|---|---|---|
| Catalogue | At least 1,000 unique SKUs (unique by ingredient list and variant attributes) with category, ingredient list, diet tags, allergens, price, pack size, stock, gourmet/organic flags, category icons; a generated 5,000-SKU set for the scale benchmark | Cart, engine, retriever |
| Dishes and recipes | 35 dishes now, growing to at least 127 including 100 companion-course dishes (ADR-004 v2) (Indian food and beverages, plus four clearly marked international edge-case dishes, one of them Sushi, whose key ingredients are deliberately absent from the catalogue for UJ10) with ingredients and quantities | Text, mood and photo flows |
| Pairings | Curated companion table (for example Biryani and Raita), blended with vector neighbours of the dish for add-ons (ADR-004 v2) | Culinary pairing weight |
| Trends | Time-of-week and weather multipliers | Trend lever |
| Personas | Eligibility rules per diet and faith option | Guardrails |
| Transcripts | 3 to 4 saved video transcripts | Demo |

## 7. Setup and cost summary
All required components are free: Python, Node, Ollama, GitHub, and the Gemini free tier (it needs a Google account to create an API key). There is no deployment and no hosting; the prototype runs on your laptop and lives on GitHub as a repository. The README setup guide will include one-command install and run scripts, since you are new to the terminal.

## 8. Platform risks
| Risk | Mitigation |
|---|---|
| Local model too slow or inaccurate | Benchmark Day 1; smaller model; cached demo paths |
| Gemini free-tier rate limits or model renames | Model name in `.env`; fallback chain |
| Gemini privacy conflict (C8) | Owner decision; sample photos only |
| YouTube blocks transcript fetch | Fixtures and fallbacks |
| Library breakage or version drift | Pin versions in lock files |

## 9. Sources
See `docs/core/references-and-glossary.md` (to be completed). Sources used here:
- Google AI for Developers, Gemini API pricing: https://ai.google.dev/gemini-api/docs/pricing
- `youtube-transcript-api` on PyPI (version 1.2.4, Jan 2026): https://pypi.org/project/youtube-transcript-api/
