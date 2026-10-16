# ADR-008: Choose SKU variants with the lever scores plus a price-based value term
- **Status:** Accepted (owner decisions OQ-12, OQ-13, 2026-10-17); constants to be tuned Day 1 to 2
- **Date:** 2026-10-17
- **Decision owner:** VJP (product owner); drafted by Claude
- **Authorisation:** Owner: levers must choose variants; price must carry real weight.

## Context
One ingredient (milk, bread) maps to many eligible variants. The choice must be explainable and must make lever effects visible in the cart (the brief's key requirement).

## Decision drivers
- Visible lever effect in the cart
- No new slider (Settings Panel is the source of truth)
- Cheaper options should win for budget personas
- Explainability on the cart line

## Options considered
| Option | Pros | Cons |
|---|---|---|
| Fixed default variant per ingredient | Predictable | Levers have no effect at the cart level |
| Levers only (no price) | Simple | Ignores cost; poor for the student persona |
| Levers plus value term whose weight falls as gourmet rises (chosen) | Price matters at low gourmet; premium wins at high; no new control | One more constant to tune |

## Decision
Score variants with `S_v = M_elig × [(1 − β) × Σ(ŵ_k × s_k) + β × v]`, where `v = 1 − min-max-normalised price per unit` among eligible variants, `β = β0 × (1 − gourmet_affinity)` and `β0 = 0.30` (config `VALUE_WEIGHT`). A user-named attribute ("skimmed") restricts the eligible set. Lowest price breaks remaining ties.

## Rationale
Tying the price weight to the existing gourmet slider uses a lever the user already understands and preserves the four-lever panel.

## Consequences
- **Positive:** Lever effects appear in the cart; budget behaviour emerges without a new control.
- **Negative:** β0 is a judgement value; a wrong value could mute or exaggerate lever effects.
- **Neutral:** None identified.

## Risks and mitigations
- Price swamps organic at low gourmet: AC-38 and AC-42 sensitivity tests; tune β0
- Too few variants for some ingredients: validator V8 requires at least 4 variants for lever-test ingredients

## Implementation and rollout
- `engine/variants.py` pure function with unit tests
- Cart line `reason` and alternatives from the breakdown

## Validation / rollback
Rollback: set `VALUE_WEIGHT` to 0 for levers only.

## Evidence to be measured on Day 1
| Measure | Method |
|---|---|
| Variant choice changes with gourmet, organic and persona levers | Lever sweep on 6 ingredients with at least 4 variants each |
| β0 sensitivity | Compare 0.15, 0.30, 0.45 on student and gourmet personas |
Results go in `verify/benchmarks/variant-scoring.md`.

## Related documents
PRD FR-113, 114, Appendix A; AC-38, 39, 42; Data Model section 4.
