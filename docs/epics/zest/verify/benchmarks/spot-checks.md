# Evaluation Plan §8 spot checks: reason lines and SKU audit (C67)

**Who did this.** Evaluation Plan §8 assigns both checks to the owner. On 2026-10-18 the owner directed the assistant to do them instead (C67). They are **not independent**: the same assistant wrote the catalogue generator, the tag rules, the reason prompt and this review. Read the results as a second look by the author, not as a human audit.

**Reproduce.** `.venv/bin/python scripts/benchmark/spot_checks.py` (seed 20261018) writes the samples and the mechanical checks to `eval/spot-checks/reason_lines_v1.json` and `sku_audit_v1.json`. The verdicts below are the assistant's reading of those rows.

## 1. Reason lines (20 of the 30 distinct E13 headline lines)
**Source.** `eval/results/post-hoc/c54/E13-reason-line-llama3.2_3b.json`, run 1; the 3 runs were identical. Each line was checked against the exact facts the model saw (dish tags and lever drivers, rebuilt in code with no model call). The question for each line: does it use only those facts, is it readable, and does it avoid prices, stock and health claims?

| Verdict | Count | Lines |
|---|---|---|
| Faithful and readable | 14 | RP6-1-2, RP6-1-3, RP6-2-3, RP6-4-1, RP6-4-2, RP6-5-1, RP7-1-1, RP7-1-2, RP7-1-3, RP7-2-1, RP7-2-3, RP7-4-2, RP7-5-2, RP7-5-3 |
| Template shown (validator rejected the model's line) | 2 | RP6-3-1 Jowar Bhakri, RP7-3-1 Keto Chicken Salad. Both dishes carry the `healthy` tag; the C54 claim-word rule worked |
| Minor wording | 3 | RP6-3-2 "Fresh, tangy, and aligns with…" (broken list grammar); RP7-3-3 "a perfect comfort food match" (puffery); RP7-3-2 "with gourmet and organic options available" (reads as a claim about what the catalogue stocks, from the driver "gourmet and organic match") |
| Nutrition wording echoed from a tag | 1 | RP7-4-3 Chicken Seekh Kebab "High protein and gourmet match…". It comes from the dish's `high_protein` tag, so it is grounded in catalogue data, but it is a nutrition claim. C50's list does not include "high protein", so the validator lets it through |

**Summary.**
- 18 of 20 lines were written by the model: 14 clean, 4 with minor issues.
- No line states a price, stock or an ingredient the dish lacks.
- No line invents a fact outside the tags and drivers.
- Most lines are generic ("matching mood and preferences"): true, but not very informative.

**Open for the owner.** Should "high protein" (and other nutrition-tag echoes) join the C50 claim words? It is not changed here: E13 is closed and changing it would need a post-hoc rerun.

## 2. SKU audit (103 of 1,027 variants, 10%)
### Mechanical checks (all 103 rows)
| Check | Rows failing |
|---|---|
| Keyword classes from the name and ingredients (the E7 checker) that the stored tags miss | 0 |
| Pack price more than ₹2 or 25% away from price per unit × pack size | 0 |
| Packs per variant outside one to three | 0 |
| Negative stock | 0 |

### Reading each row (name, category, ingredients, diet tags, allergens, packs, prices)
No row has a tag error that would let an ineligible item reach a persona: diet class, vegan, Jain, Satvik, halal and allergens agree with the ingredients on every row. **10 of 103 rows have a data-quality defect**, none of them guardrail-relevant:

| Kind | Rows |
|---|---|
| Misleading name or ingredient | **66** "Egg alternatives (Boiled peeled)" is a boiled egg. Tagged `egg` correctly, so the diet filters hold, but the name suggests a substitute. **62** "Frozen fruit pulp (Chikoo)" lists mango as its main ingredient. **30** "Noodles (Rice noodles)" lists refined flour first (so it carries gluten, which the tags reflect) |
| Unit or price realism | **47** Garbage bags, 30 pieces at ₹1,218 (about ₹40 a bag; implausible). **38** Chicken stock cube sold in 250 ml and 500 ml. **13** Baby corn sold by the piece |
| Tag consistency, no effect on filtering | **29** Oats (steel cut), **76** Breakfast porridge mix, **103** Oat ice cream: `gluten` allergen and `gluten_free: false`, but no `gluten` flag. The gluten filter reads `gluten_free` (`engine/eligibility.py`), so they are excluded correctly |

### Observation, not a defect
**7** Mushroom (Button) is `jain_ok`. This follows the documented rule (Data Model §9: Jain excludes meat, fish, egg, root vegetables and onion or garlic; fungi are not listed), and the lexicon notes that "some Jain and Satvik traditions avoid fungi (simplified)". Whether Jain should exclude fungi is an owner decision; changing it would change E7 inputs.

### Not fixed
The catalogue is seeded and its validators pass; changing generated data would alter the inputs of E7, E8 and E9. The defects are listed for the owner to decide.
