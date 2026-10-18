# Session handover (updated 2026-10-18, end of the block 3.1 session)

Paste everything below the line into the next Claude Code session.

---

You are continuing the build of Zest, a web-based AI sous-chef prototype (interview assignment).
Repo: /Users/varunparikh/Projects/zest-sous-chef (GitHub: VarunParikh/zest-sous-chef, branch main).
The last session (block 3.1: E2E-001, E10, E11, E14) ended with everything committed and pushed to `origin/main` (owner approved the push; ask before any future push). Block 3.1 is commits `4e5974d` onward plus this handover update (block 2.6 ended at `6b9bc05`).
Start by running `git status` and `git log --oneline -15` to confirm. Ask the owner before any future push.

## Read first, in this order
1. CLAUDE.md
2. docs/epics/zest/build-plan.md sections 3 to 8
3. docs/core/approval-register.md (Rules, then the decisions log at the bottom)
4. docs/core/open-conflicts.md (C1 to C66)
5. CHANGELOG.md
Work in plan mode for each block.

## Standing rules (from the owner; still in force)
- **No implementation without an approved spec section.** Every build-gating document is approved as of 2026-10-18; check the register for current versions. Approval Register Rule 2: if you edit an approved document in a way that changes a requirement, guardrail or decision, it goes back to "Draft (amended)" and needs the owner's re-approval before you build on it.
  - Pattern the owner has accepted: put the exact amendment text in a plan, state that approving the plan re-approves exactly that text, then record it in the register.
- **Tests before code.** Write the tests, show them failing, then implement. Report real statuses only: PASS, FAIL, BLOCKED, NOT RUN. Never skip or weaken a test to get green. If a test was wrong about the data, fix it and say so plainly.
- **Commit after each story.** Conventional commits plus a CHANGELOG line, ending with "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>". Before each commit, run the tests on the staged tree only (`git stash push --keep-index --include-untracked`, `make test`, `git stash pop`).
- **Data and guardrails.** Mock data only. Guardrails run in code after retrieval. SKUs, prices and stock come only from the catalogue. Text from videos, photos and pages is data, never instructions.
- **Ask first** before any new dependency, model download, paid API call, file outside the repo, or push. Never force-push or rebase pushed history: eval result files record commit hashes.
- **Secrets.** The owner's Gemini key is in `.env`; never print it. It travels only in the `x-goog-api-key` header. With permission the owner gave, I changed only these `.env` lines: `VISION_PROVIDER=ollama`, `VISION_MODEL=qwen3-vl:4b-instruct`, `TIMEOUT_VISION_S=60`.
- **Conflicts.** Log any document conflict in docs/core/open-conflicts.md (next ID: **C69**). Never resolve one silently.
- **Staged-tree test run:** the `git stash` sequence was blocked by the permission classifier in block 3.1. Instead, stage everything (`git add -A`), confirm `git diff --quiet` (worktree equals index), then run `make test`.

## Environment
- macOS, Apple M5, 16 GB. Python 3.12 via `.venv` (`python3` on this machine is 3.15). Node 26, npm 11.
- **Make targets:**
  - `make setup` (also runs `npm ci` in src/frontend)
  - `make app`: backend on 127.0.0.1:8000 and Vite on **http://localhost:5173**; Ctrl+C stops both
  - `make dev` (backend only), `make test`, `make test-e2e` (builds the frontend, then runs E2E-001 headless), `make test-embedder`, `make data`, `make index`, `make scan`, `make eval-decisions`
- **Last results (end of block 3.1):** `make test` 571 passed, 2 deselected (embedder, e2e), 1 xfailed. `make test-embedder` 1 passed. `make test-e2e` 1 passed. `make data` V1 to V17 PASS 17 on both sets (C68). `make scan` 0 findings. `make test-e2e` and `make test-embedder` now also write JUnit files (`e2e.xml`, `embedder.xml`) for E14.
- **Ollama models in use:** `llama3.2:3b` (text, 4k context), `llama-guard3:1b` (guard), `qwen3-vl:4b-instruct` (default vision). Others are installed but unused.
- **Preview:** `.claude/launch.json` has `zest-backend` (:8000) and `zest-frontend` (:5173). The owner usually runs `make app` in terminal tab 0, so those ports are taken. For live checks, run the app in-process (`TestClient(create_app(load_settings()))`) instead of starting servers.
- Playwright Chromium is in ~/Library/Caches/ms-playwright (owner approved the download).

## What exists now
- **Backend (src/backend):** sessions with lever snapshots; levers config; typed cards and TurnResponse. The cart is pure code:
  - combined-need pack allocation (C33), shared and dimmed lines, quantity as a pack multiplier (C35)
  - substitution, idempotent checkout with stock and price revalidation
  - swap, Undo, and replace-or-add with Undo
- **Chat pipeline:** rules guard, then `llama-guard3:1b` (S8 and S6 ignored, ADR-006 v3), then intent (`intent_classify_v2`), then the flows:
  - **mood:** open requests use a course-wide, lever-ranked pool (ADR-004 v3); no repeats in a session
  - **text recipe:** an open dish carted message by message; named dishes match by word; persona blocks are explained
  - **YouTube:** live, then fixture, then title, then a paste prompt; transcripts are guarded as data; pantry question
  - **photo:** local qwen3-vl, Gemini opt-in, samples fallback; always confirmed before the cart changes
  - **add-ons:** one per carted dish (US-19), with Undo
  - "Why this?" cards on every suggestion, and the inspector endpoint including the add-on pool
- **Frontend (src/frontend):** React 19 + Vite 8 + Tailwind 3.4 + TS 5.9.
  - the split screen, lever accordions with effective shares, persona presets, Reset levers
  - the next-session banner, plus a "Not applied yet" tag
  - the score chart, inspector tables, chat with all card types
  - the ⓘ "why" panel, an estimated progress bar while analysing, Clear chat with confirmation
  - the cart icon with badge, the mobile-shaped Express Cart (edits, dimmed shared lines, Buy Now), and the in-window order state with a 10 s progress bar
  - the focus trap, Escape, and a segmented control below 1024 px
- **Tests:** `tests/acceptance/chat_harness.py` has `FakeOllama` (guard, intent, extraction, reason, vision and Gemini fakes) plus helpers `say`, `start`, `find(turn, template_id)`, `extraction`, `line`, `image_bytes`, `upload`. Use `find` rather than `messages[-1]`, because an add-on message usually follows the main reply.

## Decisions taken this session (details in open-conflicts and the register)
- **C30 to C32:** weights-zero notice copy and the persona-conflict rule; the client sends current levers for the banner flag; the frontend owns the Clear chat confirmation.
- **C33 to C35:** combined-need allocation (FR-71 over the Data Model); `in_stock` and `quantity` on cart lines; quantity is a pack multiplier.
- **C36, C39:** config keys (`GUARD_*`, `INTENT_CONFIDENCE_MIN`, `LIVE_TRANSCRIPTS`, `MAX_RECIPE_CHARS`); python-multipart and youtube-transcript-api added.
- **C37:** ADR-003 v3: local `qwen3-vl:4b-instruct` is the default although it FAILED E3 (photo accuracy NOT MET); Gemini opt-in; samples for the demo and as fallback; 60 s timeout.
- **C38:** MSG-PHOTO-CONFIRM, and MSG-TXT-STORED shows the stored servings (FR-32 servings scaling is CUT).
- **C40, C44:** the guard ignores the llama-guard S8 (bare YouTube links) and S6 ("what should I eat") categories. ADR-006 v3.
- **C41, C42:** cart lines carry `icon` and dishes `course` (API Spec v0.6); React type packages added (Build Plan v0.4).
- **C43:** hunger, suggestion and stove words in the rules guard; intent prompt v2; meal-aware course steering ("tonight" is dinner; plain hunger uses the time of day).
- **C45:** open requests use a course-wide, lever-ranked pool; no dish repeats within a session; the next-session rule (C4) is kept.

## Open items and known gaps
- **Push:** done; everything up to the handover commit is on origin/main.
- **Duplicate sessions:** every page load creates 2 sessions, because React StrictMode runs the startup effect twice in dev. It's harmless; the fix is a ref guard in `App.tsx`. Offered to the owner, not yet asked for.
- **Known guard false positive:** a bare unknown dish name ("make me ratatouille") is redirected as off-topic; recorded as a strict xfail.
- **Retrieval quality limits:** Hot Chocolate for "cooling for a hot day" (BM25 matches "hot"); Mango Kulfi as the add-on for Shakshuka; "Feeling cooling?" copy. All are reported, none fixed (owner decision pending).
- **Photo labels:** mock-data/photos.json labels are assistant-written and UNVERIFIED. The 10% hand audit of generated SKUs is still owed by the owner.
- **Still open conflicts:** C21 (doc-sync of the category enum), C27 (ambiguity margin, confirm with E5), C29 (E3 swap-thrash definition).
- **Interim reply:** cart edits by chat ("remove the oil"), staples answers, variant requests and cooking questions still reply MSG-UNSUPPORTED (FR-78 is a Should, first in the cut list).
- **US-27** (post-order pairing, a Should) is not built.
- **Block 2.6 done (2026-10-18), see `verify/benchmarks/block26.md`:** E8 PASS; E7 PASS (adversarial after the allocation fix `77f99ca`, post-hoc; real arm); E9 PASS; E12 FAIL at β0 0.30 (0.15 passes); E6 FAIL (gourmet inert; most soft levers below 0.33); E4 rerun FAIL 11/13 (G10 passes since S6 is ignored); E2 FAIL 22/30; E13 FAIL ("healthy" claim word in 4 shown lines).
- **C53 done (post-hoc, `eval/results/post-hoc/c53/`):** dish premium rescaled, `DISH_POOL` 25, `ADDON_POOL` 12, β0 0.20, F1 substitution delta. E12 PASS; E6 still FAIL but no critical (most soft levers under 0.33; cooling trend 0.05); E7 and E8 PASS.
- **C54 done (post-hoc, `eval/results/post-hoc/c54/`):** guardrail-targeting rule, code routing, intent prompt v3, claim words in the reason validator. E13 PASS; E4 on held-out guard_v2 FAIL 14/20 with 1/10 false positives (V21 "skip the garlic for my Jain friend"); E2 FAIL 24/30; E9 and E7 PASS. The rules guard also redirects some benign dev utterances ("what does tempering mean?", "good morning").
- **C55 done (post-hoc, `eval/results/post-hoc/c55/`):** guardrail rule narrowed, S8 ignored only with a YouTube link. E4 on held-out guard_v3 FAIL 11/20 (false positive W25 from the off-topic check); E9 and E7 PASS.
- **Accepted as known limitations (owner, in `block26.md`):** E4 guard (C56 exception), E2 intent 24/30 (C55) and E6 soft-lever sensitivity (C57). Block 2.6 is closed. The earlier E4 S6, E2 prompt and E13 questions were settled by C54. Any change is rerun post-hoc with the first results kept. Owner spot check of 20 reason lines still owed.
- **NOT RUN:**
  - evaluations E10, E11, E14
  - V7 stock scenarios (no stock_scenarios.json)
  - demo endpoints 14 and 15
  - make targets test-full, coverage, eval, report
  - qwen3-vl:8b in E3 (owner decision)

## Block 2.6 in one paragraph
Evaluation harnesses live in `scripts/benchmark/` (pure parts in `src/backend/evaluation/`); run them in-process (`scripts/benchmark/_app.py`), never on ports 8000 or 5173. Results: `eval/results/` (first runs) and `eval/results/post-hoc/{c53,c54,c55}/` (reruns after owner decisions; first results are always kept). Report: `docs/epics/zest/verify/benchmarks/block26.md`. Final statuses: E7, E8, E9, E12, E13 PASS; E2 (intent 24/30), E4 (guard 11/20 on held-out guard_v3) and E6 (soft levers under the 0.33 gate) FAIL as owner-accepted known limitations (C55, C56, C57). Settings changed: `DISH_POOL` 25, `ADDON_POOL` 12, `VALUE_WEIGHT` 0.20 (also in the owner's `.env`), `GUARD_IGNORE_CATEGORIES` S6 plus `GUARD_IGNORE_IF_LINK` S8. Lessons: grep for hard-coded constants across all test markers (embedder and e2e too) when a config value changes; check `make test` output for any `FAILED` line or make error before committing, not just the last line; a dataset whose results have been seen is contaminated for any later change.

## Block 3.1 in one paragraph
Report: `docs/epics/zest/verify/benchmarks/block31.md`.
- **Results:** E2E-001 PASS; E10 PASS (26 of 26 pre-registered fault scenarios in `faults_v1.json`, 3 runs each, real models for unfaulted calls, Gemini never contacted); E11 PASS (6 flows, 10 of 10 normal runs; mood 1.2 s, text 5.1 s, YouTube 5.6 s with p95 11.0 s, photo upload 7.6 s with p95 12.5 s, sample photo 0.27 s, cart edits ≤ 16 ms); E14 PASS (33 of 33 Must stories, 45 of 45 ACs; accepted FAILs E2, E3, E4, E6).
- **Decisions:** C58 to C65 were approved with the plan: Evaluation Plan v0.6 §4.16, PRD v0.8, Conversation Design v0.4, Architecture v0.10, Data Model v0.5. C66 (owner): Agent Design v0.5 retry columns match the code.
- **Code:** `llm_call` carries `call` and `outcome`; the guard and vision providers trace too; `OllamaClient.generate` needs `call=`. Harnesses: `scripts/benchmark/resilience.py`, `resilience_ui.py`, `latency.py`, `traceability.py`. `eval/headline.yaml` names each evaluation's verdict file (owner reviewed).
- **Tests:** T-103 and T-104 added.
- **Lesson:** E14 reads IDs only from test names and docstrings, so tag new tests there, not in inline comments.

## Open items after block 3.1
- **NFR-01 latency targets:** approved and recorded in ADR-002 and ADR-003.
- **Spot checks (C67, C68):** done by the assistant, not independent (`verify/benchmarks/spot-checks.md`). The owner decided:
  - 1A: "high protein" stays and **must be listed in Known Limitations (block 3.3)**.
  - 2A: Jain excludes fungi (done).
  - 3B: validators V15 to V17 added and the catalogue fixed by rule (done). The C68 reruns left every status unchanged, and E14 still passes; `eval/headline.yaml` points to `post-hoc/c68/`.
- **Still NOT RUN:** V7 stock scenarios; demo endpoints 14 and 15; `make` targets `test-full`, `coverage`, `eval` and `report`; `qwen3-vl:8b` in E3 (owner decision); chat cart edit in E11 (C59); live YouTube in E11.

## Block 3.2 in one paragraph (closed 2026-10-19)
**Report:** `docs/epics/zest/verify/report/index.html` (and `report.md`), built by `make report` (`scripts/eval_report.py`, `backend.evaluation.report`) from `eval/results/`, `eval/headline.yaml` and `eval/thresholds.yaml` v4. Rebuilding unchanged inputs gives identical output.

**Results:**
- Overall FAIL under Evaluation Plan §7 (C70).
- No open FAIL and no critical failure.
- Accepted FAILs: E2 (C55), E3 (C37), E4 (C56), E6 (C57).
- No required evaluation without a result (C69).

**Owner review:** the owner reviewed the published page and confirmed the numbers. Five numbers recomputed by hand: `verify/benchmarks/block32.md`.

**Found and fixed:**
- Five benchmark scripts dropped `--post-hoc`; a test now guards every save call.
- Chart layout issues, found by rendering the report.

**Rebuild rule:** after any new result or headline change, rebuild with `make report`. `make eval` reruns every harness; it is long, and E11 needs other apps closed.

## Block 3.3 in one paragraph (done 2026-10-19)
**Written, from actual results:**
- `README.md`, checked from a clean clone: setup, index (one transient download failure, retry succeeded), tests, e2e, embedder, data and health all succeed
- `docs/epics/zest/release/demo-script.md`: 10 steps, each input dry-run in-process with the real models
- `docs/epics/zest/release/known-limitations.md`: limitations plus a model-card style Responsible-AI note
- `docs/epics/zest/release/prototyping-feedback.md`: its section 5, rehearsal feedback, is **pending block 3.4**

**Decisions:**
- C72: demo endpoints 14 and 15 cut; rehearsal step 6 and T-105 NOT RUN.
- C73: release documents live in `release/`.
- C74: Security Note wording synced to C37.

**Found and fixed:**
- The seed-check scripts did not know the C68 markers, so `make data` had failed since `a9cb089` (records corrected).
- `doc_check` missed make targets that contain digits.

**New tool:** `python -m scripts.doc_check` checks the release documents' links, make targets and cited IDs.

**Report:** the committed evidence report shows HEAD `b657d04`. Rebuild it with `make report` at release (block 3.5); only its HEAD and staleness counts change.

## Block 3.5 status (2026-10-19)
**Done:**
- Security Note §7 blockers 1a and 2 to 7 PASS, with evidence in `docs/epics/zest/release/release-checklist.md`.
  - New tests: T-075 (markup renders inert, E2E) and the image-text injection test, alongside T-103 and T-104. Each covers existing behaviour and passed on its first run.
- E14 rerun post-hoc (`eval/results/post-hoc/block35/`): PASS. The Test Plan parser now reads annotated priorities ("P0 (E2E)").
- Evidence report rebuilt.
- Reviewer path checked from a fresh clone: setup, index, tests, `make app`, health, and a real chat through the frontend. The README now lists the fresh-Mac prerequisites and has a screenshot.
- Found and disclosed: a message sent immediately after "Start new chat" goes to the deleted session; the app recovers, but the message is lost (Known Limitations).

**Owner items:**
- **1b:** done; the owner confirmed on 2026-10-19 that the Day-0 Gemini key is revoked.
- **Block 3.4 rehearsals: TO DO (deferred by the owner on 2026-10-19).** Run the Test Plan §9 checklist twice with `docs/epics/zest/release/demo-script.md`, skipping step 6 (C72). Then the network-off test and a backup screen recording. Write the results into `prototyping-feedback.md` §5.
- **Tag `v0.1.0` and push:** done 2026-10-19 with owner approval. The CHANGELOG `[0.1.0]` section was cut in the tagged commit.

**Possible follow-up, not asked for:** lock the chat input while a new session starts. A ref guard in `App.tsx` for the duplicate development sessions also needs owner approval.
