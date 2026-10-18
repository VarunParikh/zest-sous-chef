# Block 3.2: evidence report

**Report.** `docs/epics/zest/verify/report/index.html`, plus `report.md` for GitHub. It is built by `make report` (`scripts/eval_report.py`) at commit `09f0d5d` (code `b657d04` plus the chart-layout fix), from `eval/results/`, `eval/headline.yaml` and `eval/thresholds.yaml` v4 (Evaluation Plan v0.7 §4.17, C69 to C71). Rebuilding unchanged inputs gives byte-identical output.

## Gate
- `make report` exits 0: **no required evaluation is without a result** (C69).
- The only NOT RUN on the page is the `qwen3-vl:8b` arm of E3, which was not run by owner decision; it is listed, not counted.
- **Overall status: FAIL**, applying Evaluation Plan §7 as written (C70).
  - No open FAIL.
  - No critical failure.
  - Accepted FAILs: E2 (C55), E3 (C37), E4 (C56), E6 (C57).

## Five numbers recomputed by hand (Evaluation Plan §8)
**Method.** 5 of 9 candidate metrics were picked with seed 20261018. Each was recomputed from the result's per-example rows (not from its `metrics` block) and checked against the text the report prints.

| Metric | Recomputed | Shown in the report | Match |
|---|---|---|---|
| E4 attack block rate (median run, guard_v3) | 0.5500 | `0.55` | yes |
| E7 real-arm surfaces checked | 24854 | `24854` | yes |
| E7 real-arm violations | 0 | `0 violations in 24854 checks` | yes |
| E11 photo-upload p95 | 12547.9 ms | `12.55 s` | yes |
| E9 ingredient precision (median run) | 0.9793 | `0.98` | yes |

## Found while building
**Five benchmark scripts dropped `--post-hoc`** (`levers.py`, `variants.py`, `retrieval.py`, `text_models.py`, `vision.py`).
- **Effect:** the E6 and E12 reruns (C53, C68) were filed under `post-hoc/`, but their notes lack the POST-HOC marker.
- **Fix:** every `save` call now passes the reason, and a test guards all scripts. The report treats any file under `post-hoc/` as post-hoc and says that its reason was not recorded.
- **Existing result files are unchanged.** The C68 E5 rerun was marked, because the reason was passed via `--notes`.

## Owner review
**Confirmed by the owner on 2026-10-19:** the owner reviewed the published report and confirmed the numbers. Block 3.2 is closed.
