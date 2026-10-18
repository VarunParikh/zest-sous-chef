# Session handover (updated 2026-10-18, end of the block 2.6 session)

Paste everything below the line into the next Claude Code session.

---

You are continuing the build of Zest, a web-based AI sous-chef prototype (interview assignment).
Repo: /Users/varunparikh/Projects/zest-sous-chef (GitHub: VarunParikh/zest-sous-chef, branch main).
The last session (block 2.6, evaluations) ended with everything committed and pushed to `origin/main` (owner approved the push). Block 2.6 is commits `6c1d115` to `23e2a7f` plus this handover update (block 2.5 ended at `a75d825`, block 2.4 at `c18b5c0`).
Start by running `git status` and `git log --oneline -15` to confirm. Ask the owner before any future push.

## Read first, in this order
1. CLAUDE.md
2. docs/epics/zest/build-plan.md sections 3 to 8
3. docs/core/approval-register.md (Rules, then the decisions log at the bottom)
4. docs/core/open-conflicts.md (C1 to C45)
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
- **Conflicts.** Log any document conflict in docs/core/open-conflicts.md (next ID: **C58**). Never resolve one silently.

## Environment
- macOS, Apple M5, 16 GB. Python 3.12 via `.venv` (`python3` on this machine is 3.15). Node 26, npm 11.
- **Make targets:**
  - `make setup` (also runs `npm ci` in src/frontend)
  - `make app`: backend on 127.0.0.1:8000 and Vite on **http://localhost:5173**; Ctrl+C stops both
  - `make dev` (backend only), `make test`, `make test-e2e` (builds the frontend, then runs E2E-001 headless), `make test-embedder`, `make data`, `make index`, `make scan`, `make eval-decisions`
- **Last results (end of block 2.6):** `make test` 513 passed, 2 deselected (embedder, e2e), 1 xfailed. `make test-embedder` 1 passed. `make test-e2e` 1 passed (frontend build clean). `make data` V1 to V14 PASS 14 on both sets. `make scan` 0 findings.
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

## Next: Day 3, block 3.1 (build-plan section 5)
E2E-001 (passes today), **E10** fault injection (Gemini down, transcript blocked, vector store disabled, model invalid JSON, model timeout, backend slow: each takes its defined fallback message, no crash, no success message; pass rule 100%), **E11** latency (per flow, 10 runs after warm-up, median and p95 with the `llm_call` breakdown; targets come from E1 and are recorded, never invented), **E14** traceability (every Must story has a test, every AC maps to a test or evaluation, no open FAIL). Gate: pass or documented.

Points to raise with the owner before building (log as C58 onward):
- E14's rule "the latest results contain no open FAIL" conflicts with the owner-accepted FAILs (E2, E4, E6); decide how accepted exceptions count.
- E11 lists a "cart edit" flow, but chat cart edits reply MSG-UNSUPPORTED (FR-78 is first in the cut list); decide whether to measure the API cart edit instead or mark it NOT RUN.
- E11 should run with the owner's other apps closed (the E1 RAM floor is 3 GB free); ask the owner to stop `make app` during the latency runs.

Then block 3.2: the evidence report (`make report`, built from `eval/results/*.json` only; no NOT RUN on Must evaluations), 3.3 README and docs, 3.4 rehearsals, 3.5 release.
