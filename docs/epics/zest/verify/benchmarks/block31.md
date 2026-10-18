# Block 3.1 results (E2E-001, E10, E11, E14)

Run 2026-10-18 on the target laptop (Apple M5, 16 GB), in-process, against Evaluation Plan v0.6 §4.16 (C58 to C66). Every number below comes from a file in `eval/results/` (per-example data inside), and every result records a clean tree. Statuses are real. Nothing was tuned, and no threshold or definition changed after a run.

## Summary
| Item | Status | Headline | Source |
|---|---|---|---|
| E2E-001 demo path | **PASS** | Start and end of the block (fake model, Chromium) | `make test-e2e` |
| E10 resilience | **PASS** | 26 of 26 pre-registered scenarios, each in all 3 runs (78 of 78 runs); no crash, no false success | `E10-resilience-real-stack.json` (commit `dae01e2`) |
| E11 latency | **PASS** | All 6 flows: 10 of 10 runs with the normal reply, no fallback, no timeout | `E11-latency-real-stack.json` (commit `31f4bc5`) |
| E14 traceability | **PASS** | 33 of 33 Must stories and 45 of 45 ACs link to passing tests or headline evaluations; no open FAIL; 4 accepted FAILs | `E14-traceability.json` |

## E10 resilience
- **Faults injected:** at the model transport (`FaultProxy`), the transcript chain's live fetcher, the vector store, and in-process timeout settings.
- **Unfaulted calls** went to the real `llama3.2:3b`, `llama-guard3:1b` and `qwen3-vl:4b-instruct`.
- **Gemini was never contacted.** Its scenarios used a placeholder key, and the proxy refuses any non-local host.
- **Coverage:**
  - Gemini down, rate-limited and timing out (F01 to F03)
  - local vision unreachable, at a real 0.1 s deadline, and invalid (F04 to F06)
  - transcript blocked with a fixture, title only, and nothing (F07 to F09)
  - vector store failing to build and failing mid-session (F10, F11)
  - invalid JSON on intent, extraction (text and YouTube), reason and guard (F12 to F16)
  - timeouts on the same calls (F17 to F21)
  - a real 0.1 s text-model deadline (F22)
  - Ollama unreachable (F23)
  - a slow dependency with a concurrent second message, which got 409 `SESSION_BUSY` with no state change (F24)
  - the browser: a slow reply keeps the input locked (F25); an aborted request and a bare 500 both show MSG-SERVER with the cart left empty (F26)
- **Attempt counts** match C62 and C66:
  - Gemini 503 or 429: 2 attempts
  - every timeout: 1 attempt
  - invalid intent, extraction and reason: 2 attempts
  - invalid local vision: 1 attempt
- **Plumbing check:** before the scored run, F01, F12, F17, F24, F25 and F26 were run once into a scratch folder. They were not scored, and nothing changed afterwards.

## E11 latency (server-side wall clock per API call; browser rendering excluded)
The owner closed other apps. Free RAM was 5.92 GB before the run and 1.39 GB after (all three models resident). p95 uses linear interpolation; with n = 10 it sits near the maximum.

| Flow | Median | p95 | Max | Cold start | Model time, median (p95) |
|---|---|---|---|---|---|
| Mood (levers_v1 L01 to L10) | 1.20 s | 1.25 s | 1.27 s | 3.9 s | intent 0.62 s, reason 0.47 s, guard 0.05 s, other 0.05 s |
| Text recipe (carts_v1 text rows) | 5.06 s | 5.52 s | 5.59 s | 6.4 s | extract 4.12 s (4.59), intent 0.71 s, guard 0.07 s |
| YouTube, fixture path (4 videos) | 5.62 s | 11.03 s | 11.78 s | 5.4 s | extract 5.27 s (10.36), guard 0.20 s |
| Photo upload, local qwen3-vl (RF01, 02, 03, 07; upload plus confirm) | 7.58 s | 12.55 s | 13.41 s | 8.0 s | vision 7.31 s (12.18) |
| Sample photo (the demo path) | 0.27 s | 0.33 s | 0.33 s | 0.22 s | guard 0.07 s |
| Cart edits (API): quantity / remove / swap / Undo | 4 / 2 / 15 / 2 ms | 5 / 2 / 16 / 2 ms | | | none |

### Comparisons (not gated, C60)
- **Extraction:** text extraction (median 4.1 s, p95 4.6 s) is in line with E1 (4.2 s, 5.4 s).
- **YouTube extraction:** its p95 of 10.4 s is twice that. The slow runs are all video V4 (meal prep, the longest transcript: 10.1 s and 11.8 s).
- **Photo vision:** the call's p95 of 12.2 s is inside the E3 gate (p95 ≤ 20 s) and the 60 s timeout. This is much better than the E3 benchmark's 109.8 s p95, but E11 used the 4 demo photos, not the E3 set, so the two are not comparable. E3 stays NOT MET (C37).

### Not run
- The chat cart edit (FR-78 cut, C59).
- Live YouTube fetch (network).

### Proposed NFR-01 targets (for owner approval; not yet in ADR-002 or ADR-003)
These are the measured p95 values rounded up, as regression limits on this laptop:

| Flow | Proposed p95 target |
|---|---|
| Mood | 1.5 s |
| Text | 6 s |
| YouTube (fixture) | 12 s |
| Photo upload, local | 15 s |
| Sample photo | 0.5 s |
| Cart edits | 50 ms |

## E14 traceability
**Inputs:**
- User Stories v0.5
- PRD AC table
- Test Plan §4 and §5
- 441 test functions (574 cases with parameters) in the JUnit files from `make test`, `make test-e2e` and `make test-embedder`
- `eval/headline.yaml` (owner reviewed 2026-10-18)
- `open-conflicts.md`

**Accepted FAILs (C58):**
- E2 (C55)
- E3 (C37)
- E4 (C56)
- E6 (C57)

**Not run by owner decision:** `qwen3-vl:8b` in E3.

**Listed, not open:** the strict xfail (guard false positive on a bare unknown dish name).

**How tests are linked:** a module docstring links to every test in its module, while a function name or docstring links to that function only. Each passing link records which level it came from.

**Gaps found and closed before the scored run:**
- **T-103 and T-104** were not referenced by any test, so new tests were written. They cover existing behaviour and passed on their first run.
- **US-07** had no linked test. Its tests existed, but the links were in inline comments, so tag-only docstrings were added (T-074, FR-14).

## Integrity notes
- **Pre-registration:** `faults_v1.json` was hashed in `MANIFEST.json` (commit `a2fdc36`) before the E10 harness existed.
- **Document conflicts:** C66 (retry columns) was found while writing it and decided by the owner first.
- **Tests first:** the unit tests for `resilience`, `latency` and `traceability`, and the C61 tracing tests, were shown failing before their code. One latency test had wrong arithmetic in its expected value; the test was corrected, not the code.
- **Hand recompute:** 5 numbers were recomputed by hand from the per-example data, and all match: mood median, text p95, swap median, E10 passing runs, E14 stories.
- **Still owed by the owner:** the 20-line reason spot check and the 10% SKU audit.

## Reproduce
```
.venv/bin/python scripts/benchmark/resilience.py --runs 3
.venv/bin/python scripts/benchmark/latency.py --runs 10      # stop make app and close other apps first
make test && make test-e2e && make test-embedder
.venv/bin/python scripts/benchmark/traceability.py
```
