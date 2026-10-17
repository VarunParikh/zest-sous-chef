# ADR-004 (v2): Hybrid retrieval, extended to add-on suggestions with curated pairs plus vector neighbours
- **Status:** Accepted; **amended 2026-10-17 (v2)** by owner decision. v1 (hybrid retrieval for ingredient and mood-to-dish lookups) stays in force and is kept below under "v1 record". The Day-1 benchmark gate now also covers the add-on evidence listed in the v2 amendment.
- **Date:** 2026-10-17
- **Decision owner:** VJP (product owner); drafted by Claude
- **Authorisation:** v1: owner instructed use of a local vector database where possible and approved a BM25 library dependency (G3). v2: owner decisions of 2026-10-17 listed below.

## v2 amendment (2026-10-17, owner decisions)
**Owner decisions:**
- Add-ons are dishes, suggested for a dish the user is cooking. Missing ingredients (from YouTube or photos) stay on the existing path and are not add-ons.
- Curated and vector signals are blended by weighted rank fusion with a course filter.
- Claude Code increases the mock companion pool; owner target: 100 companion-course dishes.
- This is an amendment to ADR-004, not a new ADR.

**Decision.**
1. **Two candidate lists** for each add-on request:
   - *Curated:* companions of the cart dish from `pairings.csv`, ranked by `strength`.
   - *Vector:* the nearest neighbours of the cart dish's stored embedding in `zest_dishes`. No new embedding or collection is needed. The dish itself and dishes already in the cart are excluded.
2. **Course rule.** A code rule applies to the vector list only: a candidate must be of a companion course. The initial set is side, beverage and dessert (config `ADDON_COURSES`); how bread is classified must be confirmed against the seed data.
3. **Fusion.** Weighted reciprocal rank fusion: `score = Σ w_i / (k + rank_i)`, with `k = 60` as in FR-110. The curated list starts at weight 2 and the vector list at weight 1 (config values, tuned by the benchmark). A dish in one list scores from that list alone.
4. **Scoring.** The fused rank feeds the add-on `s_p` through the existing rank-based normalisation (PRD Appendix A). Ties break by curated strength, then ID. The other score components and the four lever weights are unchanged.
5. **Guardrails unchanged.** Eligibility (diet, faith, specialised diet, stock, add-on price cap) runs in code after fusion on every candidate (G9, FR-112). Add-ons are never added without a tap (FR-64).
6. **Fallback.** If the vector store or embedder is unavailable, the curated list alone is used (FR-117, `fallback_used` traced).
7. **Pool.** Owner target: 100 companion-course dishes (side, beverage, dessert), up from 8 in the current seed data. Claude Code adds the dishes, their ingredients and any lexicon and taxonomy entries in the Day-1 data block (build plan 1.2) so the add-on pool exceeds the number shown (FR-111). Data validators V1 to V14 still apply, and the vector arm is evaluated against the enlarged set.

**Why.** Curated pairs are reliable but sparse: in the current seed data 25 of 35 dishes have one, and sushi (D35) has none. Vector similarity covers every dish but confuses "similar" with "goes well with", hence the course rule. Merging ranks avoids calibrating two incomparable scales.

**Costs.** More constants to tune. The course rule only partly fixes the similar-versus-complementary problem. At the original 35 dishes the vector arm adds little; it needs the enlarged pool. The target of 100 companion dishes is about twelve times the current 8 and enlarges the Day-1 data work: build it in tranches and apply the build-plan cut order (section 8) if the Day-1 gates slip. Seed counts documented elsewhere (35 dishes, about 60 pairings) will change.

**Dependencies.** None new. ADR-005 is unchanged: same Chroma collection (`zest_dishes`) and the same embedder.

**Evidence (Day 1 to 2; results go in `verify/benchmarks/retrieval.md`)**

| Measure | Method |
|---|---|
| Curated pairs recovered | Share of curated pairs in the fused top N |
| Coverage | Share of dishes with no curated pair that get at least one eligible add-on |
| Course-rule pass rate | Share of vector proposals that satisfy the rule |
| Weight sweep | Curated:vector at 1:1, 2:1, 3:1 |
| Fallback | Vector disabled: curated-only still works |

Decision rule: if the vector arm adds no eligible add-on for the dishes without curated pairs, the owner decides whether to keep it.

**Downstream documents** that still describe the add-on `s_p` as curated pairing strength only are logged as conflict C16 and are overridden by this ADR until synced: PRD (FR-62, Appendix A, FR-117, new acceptance criteria), Data Model (sections 5.4, 7.4, 8.6), Architecture (sections 5, 6), US-19, Test Cases and Test Plan, Evaluation Plan (E5, E6), Build Plan, Mock Data Plan and the Approval Register. The wording of the Settings Panel's Culinary Pairing Weight versus vector similarity is logged and resolved as conflict C17.

## v1 record (still in force)
**Original title:** ADR-004: Use hybrid retrieval: BM25 plus vector similarity, merged by reciprocal rank fusion
**Original status:** Accepted (owner decision, 2026-10-17, reversing the earlier future-scope decision; conflict C12); benchmark gate to be run Day 1

## Context
Ingredient-to-SKU and mood-to-dish lookups must handle regional names, near-identical variants and mood language over 1,000+ variants and about 34 dishes (the count when v1 was written; 35 in the seed now, at least 127 under v2). Lexical matching alone cannot match "something cooling" to Chaas.

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
PRD section 11, FR-110 to 117; Data Model section 7; Constitution G9; Risk R21, R24. v2 adds: PRD FR-62, 64, 66 and Appendix A; Data Model section 5.4; conflicts C16 and C17 in `docs/core/open-conflicts.md`.
