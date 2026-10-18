# ADR-008 (v2): Choose SKU variants with the lever scores plus a price-based value term
- **Status:** **Accepted v2, 2026-10-18 (owner decision C53, approved with its plan): `β0 = 0.20` from E12.** v1 accepted (owner decisions OQ-12, OQ-13, 2026-10-17)
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
Score variants with `S_v = M_elig × [(1 − β) × Σ(ŵ_k × s_k) + β × v]`, where `v = 1 − min-max-normalised price per unit` among eligible variants, `β = β0 × (1 − gourmet_affinity)` and `β0 = 0.20` (config `VALUE_WEIGHT`; was 0.30). A user-named attribute ("skimmed") restricts the eligible set. Lowest price breaks remaining ties.

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

## Evidence and decision (E12, 2026-10-18; v2)
At 0.30 the organic effect showed on 3 of 6 lever-test ingredients and price overrode organic for every ingredient at gourmet 0, so it failed the gate. 0.10, 0.15 and 0.20 pass (organic 5/6, gourmet 6/6, price 4/6, no override); 0.25 fails. 0.20 is the largest passing value. The values between 0.15 and 0.30 were checked after the first E12 results; E12 is the tuning sweep (OQ-13), not a held-out test. Results: `eval/results/E12-variant-sweep.json`, `verify/benchmarks/block26.md`.

## Related documents
PRD FR-113, 114, Appendix A; AC-38, 39, 42; Data Model section 4.
