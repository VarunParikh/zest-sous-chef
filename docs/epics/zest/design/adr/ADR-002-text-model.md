# ADR-002: Choose the local text model for intent and ingredient extraction
- **Status:** Proposed (to be measured Day 1)
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
**Not yet decided.** The model is the one that passes the gate below with the best latency. If none passes, the owner decides between a simpler extraction schema, shorter prompts, or a smaller model (no cloud fallback, per the owner).

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

## Related documents
PRD NFR-01, 10, 11; Risk Register R1; Architecture section 6.
