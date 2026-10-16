# ADR-004: Use hybrid retrieval: BM25 plus vector similarity, merged by reciprocal rank fusion
- **Status:** Accepted (owner decision, 2026-10-17, reversing the earlier future-scope decision; conflict C12); benchmark gate to be run Day 1
- **Date:** 2026-10-17
- **Decision owner:** VJP (product owner); drafted by Claude
- **Authorisation:** Owner instructed use of a local vector database where possible and approved a BM25 library dependency (G3).

## Context
Ingredient-to-SKU and mood-to-dish lookups must handle regional names, near-identical variants and mood language over 1,000+ variants and about 34 dishes. Lexical matching alone cannot match "something cooling" to Chaas.

## Decision drivers
- Recall of the right candidates
- The levers must have a wide pool to reorder (FR-111)
- Guardrails must stay in code (G9)
- Explainable results for the inspector
- Latency and memory on a laptop

## Options considered
| Option | Pros | Cons |
|---|---|---|
| Lexical + synonym table only | Fast, exact, explainable | Misses mood and paraphrase |
| Vector only | Handles meaning | Weak on exact and regional tokens; harder to explain |
| Hybrid BM25 + vector, fused with RRF | Complementary strengths; rank-based fusion needs no score calibration | Two indexes; more to test |

## Decision
Use hybrid retrieval. A BM25 library provides the lexical part (the library is chosen at install, candidate `rank-bm25`, and pinned). Chroma provides the vector part. Results are fused with reciprocal rank fusion (k = 60 initially) into a pool of 15 dishes or 10 variants. Retrieval returns IDs only; guardrails and levers run after it.

## Rationale
RRF merges ranks, not raw scores, which avoids calibrating BM25 and cosine scores against each other. Published benchmarks show lexical retrieval is a strong baseline and dense retrieval is not always better out of domain, so the benchmark below decides whether hybrid earns its place.

## Consequences
- **Positive:** Handles mood language and near-variant SKUs; transparent through the inspector.
- **Negative:** More components; extra dependency; index build step.
- **Neutral:** None identified.

## Risks and mitigations
- Hybrid is not better than lexical on our data: record the result; the owner decides the default; the lexical-only fallback (FR-117) always remains
- Wrong guardrail outcomes: filters run in code after retrieval (G9)

## Implementation and rollout
- `retrieval/` module with BM25, vector and fusion behind the `Retriever` interface
- Evaluation set of about 60 queries with expected IDs
- Trace event `retrieval_candidates`

## Validation / rollback
Rollback: set retrieval mode to lexical-only in config.

## Evidence to be measured on Day 1
| Measure | Method |
|---|---|
| Recall at 5 and at pool size | About 60 queries (ingredient, regional, mood, variant) for lexical only, vector only and hybrid |
| Latency | Query time at 1,000 and 5,000 variants |
| Fusion constant | Compare k = 20, 60, 100 |
Results go in `verify/benchmarks/retrieval.md`. Decision rule: if hybrid does not beat lexical on recall at the pool size, the owner decides the shipped default.

## Related documents
PRD section 11, FR-110 to 117; Data Model section 7; Constitution G9; Risk R21, R24.
