# Post-hoc reruns after C53 (2026-10-18)
Reruns after the owner's C53 decisions (A2 dish premium rescaled, B2 `DISH_POOL` 25 and `ADDON_POOL` 12, C2 β0 0.20) and fix F1, at commit `c53cfb2`. First results stay in `eval/results/`.

`E12-variant-sweep-harness-error.json` is kept but is **not a result for the shipped β0**: the E12 script hard-coded 0.30 as the shipped value and swept only 0.15, 0.30 and 0.45, so its status describes 0.30 again. The script now reads the shipped β0 from settings and adds it to the sweep; the corrected rerun is `E12-variant-sweep.json`.
