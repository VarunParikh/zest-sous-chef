# ADR-002: Choose the local text model for intent and ingredient extraction
- **Status:** **Accepted (owner, 2026-10-18):** NFR-01 latency targets recorded from E11 (owner approved 2026-10-18). `llama3.2:3b` with a 4,096-token context, chosen by the Day-1 benchmark E1 (post-hoc 4k rerun)
- **Date:** 2026-10-17
- **Decision owner:** VJP (product owner); drafted by Claude
- **Authorisation:** Owner decided: local text model only, no cloud text fallback (2026-10-17). The specific model is not chosen.

## Context
Intent classification, recipe and ingredient extraction, short replies and mood tagging run on a local model through Ollama on 16 GB RAM shared with Chroma and the backend. Extraction must return schema-valid JSON (G5). Risk R1 (model too slow or inaccurate) is the project's top-scored risk.

## Decision drivers
- Extraction accuracy on Indian recipes with Hinglish names
- Schema validity rate (with one retry)
- Latency and time to first token on the Mac
- Memory headroom beside the backend and vector store
- Free, local, offline (Constitution P9)

## Options considered
Candidates: two to three small instruction-tuned models available in the Ollama library on the benchmark day. **Exact model names are not fixed here because the library changes; they are confirmed at benchmark time and recorded in the results file.**

## Decision
**Decided 2026-10-18:** `LLM_MODEL=llama3.2:3b`, `LLM_NUM_CTX=4096`. No candidate passed at Ollama's default 16k context; the owner chose the build plan's fallback (a shorter context) and the post-hoc rerun of `llama3.2:3b` passed every E1 gate. Evidence and caveats below.

## Rationale
The decision follows the gate. The reviewer's question "why this model" is answered by the results table, which the benchmark script regenerates.

## Consequences
- **Positive:** A defensible, data-backed model choice.
- **Negative:** Choice is deferred until Day 1; prompts may need tuning per model.
- **Neutral:** None identified.

## Risks and mitigations
- No model passes: escalate to the owner on Day 1 (R1)
- Prompt overfitting to benchmark prompts: use a held-out set of prompts

## Implementation and rollout
- `scripts/benchmark/text_models.py` runs the prompt set against each candidate
- Model name is config only (`LLM_MODEL`)
- Warm-up script before the demo

## Validation / rollback
Rollback: change `LLM_MODEL` in config; no code change.

## Evidence to be measured on Day 1
| Measure | Method | Proposed gate (to confirm) |
|---|---|---|
| Ingredient extraction F1 | 10 recipe prompts (6 English, 2 Hinglish, 2 noisy transcripts) vs hand labels | At least 0.80 |
| Schema validity | Share of replies valid after one retry | At least 95% |
| Latency | Time to first token; total per extraction; p95 over runs | Targets set from results and recorded here |
| Memory | Peak resident memory with Chroma loaded | Leaves at least 3 GB free |
Results go in `verify/benchmarks/text-models.md`. The gate values above are my proposals and are not sourced.

## Evidence and decision (Day 1, 2026-10-18)
Approved by the owner on 2026-10-18 ("Approve the ADR-002, 004, 005 and 006 proposals as written"). Evidence: `eval/results/` and `verify/benchmarks/` (see [adr-proposals.md](../../verify/benchmarks/adr-proposals.md)).

- **Decision:** `LLM_MODEL=llama3.2:3b`, `LLM_NUM_CTX=4096`.
- **Evidence (E1, test split, 5 recipes):**
  - First run, Ollama's default 16k context: no candidate passed.
    - `llama3.2:3b` met F1 (0.86), schema validity (5/5) and invention (0/41), but free RAM after was 2.12 GB against the 3 GB gate.
    - `qwen2.5:7b` failed: F1 0.55, valid JSON 3/5.
    - `qwen3:4b-instruct` failed: F1 0.40, valid JSON 2/5. Both Qwen models failed validation on the Hinglish and transcript rows.
  - Post-hoc rerun (owner decision): `llama3.2:3b` at 4k context, other apps closed. **All gates pass:**
    - F1 0.86; schema 5/5 (95% CI 0.57–1.00, not separable).
    - Quantities 26/27; invention 0/41.
    - Free RAM after 6.7 GB; latency median 4.2 s, p95 5.4 s.
- **Caveats:**
  1. Two things changed in the rerun, a smaller window and closed apps. With 4k, Ollama held the model at 2.6 GB instead of 4.0 GB; free RAM before loading also rose from 5.4 GB to 7.9 GB.
  2. n = 5, so every interval is wide.
  3. Hinglish rows scored lower (F1 0.71 to 0.91).
  4. Live YouTube transcripts can exceed 4k tokens, so the video flow must cap the transcript length it sends (block 2.4).
- **Latency target (E1 says to record it here):** the extraction call is about 4–5 s (p95 5.4 s). E11 sets the end-to-end targets per flow.
- **NFR-01 end-to-end targets (owner approved 2026-10-18, from E11; C60).** Server-side p95 per flow on the M5 MacBook Air with other apps closed, the measured p95 rounded up. They are regression limits for this laptop, not user-research thresholds:

  | Flow | E11 median | E11 p95 | Target p95 |
  |---|---|---|---|
  | Mood | 1.20 s | 1.25 s | 1.5 s |
  | Text recipe | 5.06 s | 5.52 s | 6 s |
  | YouTube (fixture path) | 5.62 s | 11.03 s | 12 s |
  | Sample photo | 0.27 s | 0.33 s | 0.5 s |
  | Cart edits (API) | 2 to 15 ms | 2 to 16 ms | 50 ms |

  The photo-upload target is in ADR-003. Source: `eval/results/E11-latency-real-stack.json`, `verify/benchmarks/block31.md`.
- **Demo rule:** close other apps before the demo (Test Plan §9). The warm-up script loads `llama3.2:3b` at 4k.

## Related documents
PRD NFR-01, 10, 11; Risk Register R1; Architecture section 6.
