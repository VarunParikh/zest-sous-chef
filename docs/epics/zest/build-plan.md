# Build Plan and Handover: Zest AI Sous-Chef

Status: **DRAFT (amended) v0.3 (2026-10-18): §4 adds `python-multipart` (owner approved 2026-10-18, C39); awaits owner re-approval.** v0.2 was APPROVED (owner, 2026-10-17) (v0.1 was approved earlier the same day; v0.2 syncs to ADR-004 v2: larger dish pool and add-on retrieval) · Date: 2026-10-17 · Audience: the owner (VJP) and Claude Code
This is the bridge from documents to code. It is not one of the 25 documents; it exists because Claude Code works far better with a clear build order, gates and a first prompt.
**Honest sizing:** 40 user stories in three days is aggressive. The plan protects the demo by ordering work so the highest-value path works first and by naming what to cut. Nothing below has been built or measured.

## 1. What is done and what is not
| Done (documents) | Not done |
|---|---|
| Foundation, Discovery, Requirements, Design (conversation, architecture, 10 ADRs, data model, API, agent, security), Test Plan, Evaluation Plan | Any code, any benchmark or test result, any generated catalogue. Seed content that exists (2026-10-17): personas, a 203-term lexicon, 35 dishes (to grow, see block 1.2), a 342-product, 1,025-variant taxonomy, synonyms, pairings, trends, 4 own-written video summaries plus 6 more fixtures, 11 reference photos (labels unverified), draft evaluation datasets and thresholds |
| Written during the build (they describe what exists): README, `.env.example` (early), Demo Script, Known Limitations and Responsible-AI Note, Prototyping Feedback, CHANGELOG | |

## 2. Day 0: owner steps before Claude Code starts (about 1 hour)
Do these in order. Commands are indicative for macOS; Claude Code can run most of them, and will ask before installing anything.
1. **Rotate the Gemini API key** (the old one was pasted in chat). Create a new key in Google AI Studio and keep it somewhere private. Never paste it into chat, code or commits.
2. **Install tools** (Homebrew, Git, Python 3.12, Node LTS, Ollama, GitHub CLI). Versions change; verify current install steps on each tool's site.
3. **Create the GitHub repository** (public, empty) and note its URL.
4. **Put the project on your Mac:** unzip `zest-sous-chef.zip` (delivered with this plan), open the folder in a terminal, and run `git remote add origin <your repo URL>`. The documents' git history comes with it.
5. **Create `.env` locally** from `.env.example` (created on Day 1) and paste the new key there only.
6. **Open Claude Code** in the project folder and paste the first prompt from section 7.
7. **Approve the dependency list** in section 4 once, so Claude Code does not stop for each package.

## 3. Working method for Claude Code
- **Read first:** `CLAUDE.md`, then the documents in the order in section 6 of this plan. Do not implement anything without an approved spec section (G1).
- **One story group at a time**, tests first, commit after each story (conventional commits, with the CHANGELOG line). Use plan mode for each group, then clear context between groups so the context stays small.
- **Two parallel sessions (recommended once the API shapes are fixed):** backend and frontend, in separate git worktrees. The frontend develops against a mock server that returns the examples in the API Spec; the backend develops against the tests.
- **Stop-and-ask list:** new dependency outside the approved list; any paid API call; touching files outside the repo; changing a principle, guardrail or the Authority Matrix; any conflict between documents (log it in `open-conflicts.md`, do not resolve silently).
- **Use the skills:** `test-writer-runner` for tests, `code-reviewer` before merging each group, `doc-sync` when behaviour changes, `eval-runner` for evaluations, `guardrail-check` before pushes, `git-release` at the end.

## 4. Dependencies for one-time approval (Constitution G3)
Versions are pinned at install. Package names marked * must be confirmed on the package index before install.
| Area | Package | Purpose | Notes |
|---|---|---|---|
| Backend | `fastapi`, `uvicorn`, `pydantic`, `python-dotenv` | API, models, config | ADR-001 |
| Backend | `httpx` | HTTP client for Ollama and tests | Avoids a separate Ollama client dependency |
| Retrieval | `chromadb` | Embedded vector store | ADR-005 |
| Retrieval | `rank-bm25`* | BM25 lexical scoring | ADR-004; owner approved in principle |
| Images | `Pillow` | EXIF stripping, image validation | Owner approved 2026-10-17 |
| Integrations | `youtube-transcript-api` | Transcripts | 1.2.4 (verified current on the index 2026-10-18) |
| Backend | `python-multipart` | Multipart photo uploads (FastAPI form parser) | 0.0.32; owner approved 2026-10-18 (C39) |
| Integrations | `google-genai`* | Gemini API client (now OPTIONAL, ADR-003 v2) | Confirm the current official package name; install only if the Gemini arm is used |
| Testing | `pytest`, `pytest-playwright`, `coverage` | Tests, E2E, coverage | Test Plan |
| Frontend | `react`, `react-dom`, `vite`, `tailwindcss` | UI | ADR-010 |
| Frontend | `typescript` | Typed cards and API types | Owner approved 2026-10-17 |
Anything else needs a separate ask.

## 5. Build order
Sizes come from the User Stories (S under 1 day, M 1 to 2, L 2 to 3). Effort is per Claude Code working time, not clock time, and is my estimate.

### Day 1: foundation, data, engine, decisions
| Block | Work | Stories / evidence | Gate |
|---|---|---|---|
| 1.1 | Repo scaffold, config, `.env.example`, `make` targets, health endpoint, trace module, `.gitignore` check, secret scan | US-35 | Health page runs; scan clean |
| 1.2 | Data: generator and indexer over the seeded taxonomy (`mock-data/taxonomy/`), lexicon (203 terms, grow as needed), 1,025 variants, dishes (35 now; **build 100 companion-course dishes (side, beverage, dessert), at least 127 in total**, in tranches, with their ingredients, lexicon and taxonomy entries so every ingredient resolves), pairings (about 60 now, extended; keep some dishes uncovered), trends; validators V1 to V14; 5,000-variant set | US-36 | V1 to V14 pass; T-020 canary fails when it should |
| 1.3 | Eligibility, scoring, variant selection, context, ties | US-17, 18, 38, 28 | T-010 to T-038 pass |
| 1.4 | Retrieval: BM25, Chroma index, fusion, fallback; add-on retrieval (curated plus vector lists, course rule, weighted RRF, curated-only fallback; ADR-004 v2) | US-37, 40, 06, 19 | T-040 to T-049 pass |
| 1.5 | **Decision evidence:** E1, E3 (if key ready), E4, E5 (including the add-on arm); update ADR-002, 004, 005, 006 | Evaluation Plan | Models chosen or escalated |
**Day-1 exit (all required):** data validators green; engine and retrieval tests green; a local model passes the E1 gate (or the fallback in section 8 is invoked); the embedder decision recorded.

### Day 2: flows, API, UI
| Block | Work | Stories | Gate |
|---|---|---|---|
| 2.1 | Sessions, levers, snapshot, API skeleton with typed cards | US-01 to 04 | T-001 to T-008 |
| 2.2 | Cart: allocation, shared lines, edits, undo, checkout | US-21 to 27 | T-050 to T-062 |
| 2.3 | Guard and intent; mood flow end-to-end (the main demo) | US-05, 13 | T-070 to T-072, T-085, T-086 |
| 2.4 | Text, YouTube (fixtures first), photo (consent, sample fallback) flows | US-08 to 16 | T-080 to T-092 |
| 2.5 | Frontend (parallel session): split screen, levers, chat, cart window, inspector, banner, accessibility | US-31 to 33, 18, 39 | Renders against the mock server |
| 2.6 | Evaluations E2, E6 to E9, E12, E13 | Evaluation Plan | Lever sensitivity visible; zero persona violations |
**Day-2 exit:** every P0 test in sections 4.1 to 4.8 of the Test Plan passes; the mood demo path works in the browser with the real model.

### Day 3: prove, polish, publish
| Block | Work | Gate |
|---|---|---|
| 3.1 | E2E-001, E10 fault injection, E11 latency, E14 traceability | Pass or documented |
| 3.2 | Build the evidence report; owner reviews numbers | Report builds with no `NOT RUN` on Must evaluations |
| 3.3 | Write README (setup guide), Demo Script, Known Limitations and Responsible-AI Note, Prototyping Feedback, CHANGELOG | Reflect actual results only |
| 3.4 | Two rehearsals on the real laptop (Test Plan section 9); network-off test; backup screen recording | Checklist done |
| 3.5 | Security release blockers closed; secret scan on history; tag `v0.1.0`; push to public GitHub | Security Note section 7 |

## 6. Reading order for Claude Code
1. `CLAUDE.md`, `docs/core/constitution.md`, `docs/core/open-conflicts.md`
2. `docs/epics/zest/requirements/product-spec.md`, `user-stories.md`
3. `docs/epics/zest/design/data-model.md`, `architecture.md`, `api-spec.md`, `agent-design.md`, `conversation-design.md`, `security-privacy-note.md`, `adr/README.md`
4. `docs/epics/zest/verify/test-plan.md`, `evaluation-plan.md`
5. `docs/epics/zest/design/mock-data-plan.md`, `docs/core/product-platforms.md`, `docs/inputs/*`
Precedence when documents disagree: vision, constitution, Settings Panel, DESIGN.md and mockups, User Journeys.

## 7. First prompt for Claude Code (copy and paste)
```
You are building Zest, a web-based AI sous-chef prototype. Read CLAUDE.md first, then follow
docs/epics/zest/build-plan.md sections 5 and 6. Work in plan mode. Start with Day 1 block 1.1.
Rules: no implementation without an approved spec section; tests before code; mock data only;
guardrails in code after retrieval; never write the Gemini key anywhere except the local .env;
use only the dependencies in build-plan section 4 and ask before adding any other; log any
document conflict in docs/core/open-conflicts.md instead of resolving it silently; commit after
each story with a conventional commit and a CHANGELOG line. After each block, run the tests for
that block and report real results (PASS, FAIL, BLOCKED, NOT RUN) before moving on. Stop and ask
me if a Day-1 gate fails.
```

## 8. Cut order and fallbacks
**Protect (never cut):** the mood demo path, lever causality (US-17, 38), persona guardrails (US-28), the cart and Buy Now (US-21 to 26), the safety rules (US-05), the inspector (US-39), fallbacks (US-34, 40).
**Cut in this order if time runs short** (from the Risk Register): UJ12 add-on rejection learning (FR-65), UJ5 chat cart edits (FR-78), UJ22 live stock-out mid-chat, UJ8 non-food handling polish, UJ21 conflicting-persona self-correction, UJ57 beyond the base injection tests. Servings scaling (FR-32, Could) goes first of all.
| If this fails | Do this |
|---|---|
| No local model passes E1 | Shorten prompts, simplify the extraction schema, use a smaller model; escalate to the owner on Day 1 (no cloud text fallback) |
| Hybrid does not beat lexical (E5) | Report it; owner decides the default; lexical-only stays available (FR-117) |
| Gemini unavailable or key not ready | Use sample photos; mark E3 as NOT RUN; do not claim vision accuracy |
| Chroma memory or build time too high | Embed dishes only, variants lexical-only, and record it in ADR-005 |
| The 100-dish build slips the Day-1 gates | Ship the tranches finished; add-ons then run on a smaller pool and the shortfall is reported (ADR-004 v2 costs) |
| YouTube blocks live fetch | Fixtures (own-written narrations) are the demo path |
| Day-1 gates slip by more than half a day | Drop UJ12, 5 and the photo polish first; keep the mood path |

## 9. Daily checkpoint (every evening, 10 minutes)
Update the Risk Register scores, list the stories done and tests passing (real statuses), list gates missed, and decide cuts. Bring blocked items back to this chat for decisions.

## 10. When to come back to the chat
Return for: a failed gate; any document conflict; writing README, Demo Script, Known Limitations and Prototyping Feedback from real results; the final evidence-report review; and a last consistency check (`doc-sync`) before publishing.

## 11. Open items for the owner
Decided on 2026-10-17: TypeScript approved; publishing `docs/inputs/` (design documents and two mockup images) in the public repository approved; images are category icons plus the owner's own phone photos for the sample set.
Still needed from the owner:
1. Approve the dependency list (section 4) and this plan, through the approval register (`docs/core/approval-register.md`).
2. Done 2026-10-17: 11 reference photos supplied (the plan wanted about 6 for the app plus 15 for evaluation, so E3 intervals will be wide); 4 demo YouTube links chosen; MIT licence chosen. UJ10 decided 2026-10-17: Sushi added as dish D35, with its key ingredients deliberately absent from the catalogue.
