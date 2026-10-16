# Evaluation datasets (drafts, pre-registration)
Status: drafted 2026-10-17, **nothing has been run**. Thresholds are in `eval/thresholds.yaml`. `MANIFEST.json` holds SHA-256 hashes; commit before the first run.

| File | Evaluation | Rows | How labels were made | Known weaknesses |
|---|---|---|---|---|
| `recipes_v1.jsonl` | E1 text model | 10 (5 dev, 5 test) | English lists generated from `mock-data/dishes.csv`, so labels are exact by construction; 2 Hinglish and 2 noisy transcripts hand-written by the assistant | The English lists are templated and easier than real recipes; the Hinglish set is tiny and spelling-varied |
| `utterances_v1.jsonl` | E2 intent | 60 (30/30) | Hand-written by the assistant; 4 near-miss phrases flagged | Single author; no real user data; English only |
| `guard_v1.jsonl` | E4 guard | 40 (20/20) | Hand-written: 12 injections (4 via fake transcript text), 8 off-topic, 6 hazardous, 14 benign with sensitive-sounding words | Attacks are textbook examples; a creative attacker is not represented |
| `carts_v1.jsonl` | E9 intent-to-cart | 15 | Expected ingredient families from `dishes.csv` | 10 fixture cases use own-written narrations (V1 to V4, F05 to F25); 5 text cases are generated from `dishes.csv` at run time, so those are easier than real text |

Rules: do not tune on the test split after seeing its results; any change after the first run is logged and marked post-hoc. Labels were written by the same assistant that wrote the specification, so the owner should spot-check a sample before relying on them.

## Decisions and review status (2026-10-17)
- **Off-topic prompts** are expected to be blocked with a polite reply (owner decision). In `guard_v1.jsonl`, `expected: block` means: no action taken and a polite templated redirect shown.
- **Label review:** the owner reviewed the 20-row sample in `label_review_sample.csv` and approved the labels. Per-row verdicts were not recorded, so report this as "owner-reviewed sample of 20 of 110 utterance and guard labels; remaining labels unreviewed". Photo labels in `mock-data/photos.json` remain assistant-labelled and unverified.
