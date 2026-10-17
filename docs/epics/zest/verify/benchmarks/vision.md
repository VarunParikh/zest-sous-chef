# E3 Vision results (generated)

Commit `6e0317e` (dirty: False), 2026-10-17T20:49:56+00:00, macOS-27.0.1-arm64-arm-64bit, Python 3.12.15. All 11 photos, 3 runs each; text model and guard resident. Photo labels are assistant-written and **UNVERIFIED** (owner decision 2026-10-17).

| Candidate | Precision, clear photos (gate ≥ 0.80) | Recall, clear photos (gate ≥ 0.70) | Quality flags | Failures | Latency median / p95 (ms) | Swap-outs | Status |
|---|---|---|---|---|---|---|---|
| gemini:gemini-3.5-flash-lite | 159/207 (0.77; 95% CI 0.71–0.82) | 159/252 (0.63; 95% CI 0.57–0.69) | 30/33 (0.91; 95% CI 0.76–0.97) | 0/33 (0.00; 95% CI 0.00–0.10) | 1610 / 3486 | 0 | FAIL |
| ollama:gemma4:e2b-it-qat | 31/70 (0.44; 95% CI 0.33–0.56) | 31/252 (0.12; 95% CI 0.09–0.17) | 21/33 (0.64; 95% CI 0.47–0.78) | 12/33 (0.36; 95% CI 0.22–0.53) | 20424 / 51012 | 527 | FAIL |
| ollama:qwen3-vl:4b-instruct | 108/159 (0.68; 95% CI 0.60–0.75) | 108/252 (0.43; 95% CI 0.37–0.49) | 24/33 (0.73; 95% CI 0.56–0.85) | 6/33 (0.18; 95% CI 0.09–0.34) | 7075 / 109823 | 71575 | FAIL |
| ollama:qwen3-vl:8b-instruct | NOT RUN | | | | | | NOT RUN: owner decision 2026-10-18: skipped to save time; under the memory pressure seen with qwen3-vl:4b (about 1.1 GB swapped, p95 110 s) the larger 8B model was the least likely to pass the no-swap gate |

Test photos only (demo photos RF01, RF02, RF03, RF07 are development images):

| Candidate | Precision, test photos | Recall, test photos | Precision, demo photos | Recall, demo photos |
|---|---|---|---|---|
| gemini:gemini-3.5-flash-lite | 85/122 (0.70; 95% CI 0.61–0.77) | 85/150 (0.57; 95% CI 0.49–0.64) | 74/85 (0.87; 95% CI 0.78–0.93) | 74/102 (0.73; 95% CI 0.63–0.80) |
| ollama:gemma4:e2b-it-qat | 6/21 (0.29; 95% CI 0.14–0.50) | 6/150 (0.04; 95% CI 0.02–0.08) | 25/49 (0.51; 95% CI 0.37–0.64) | 25/102 (0.25; 95% CI 0.17–0.34) |
| ollama:qwen3-vl:4b-instruct | 51/66 (0.77; 95% CI 0.66–0.86) | 51/150 (0.34; 95% CI 0.27–0.42) | 57/93 (0.61; 95% CI 0.51–0.71) | 57/102 (0.56; 95% CI 0.46–0.65) |
