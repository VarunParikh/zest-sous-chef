# E1 Text-model results (generated)

Split: test (5 rows). Commit `4b3ae25` (dirty: False), 2026-10-17T19:48:35+00:00, macOS-27.0.1-arm64-arm-64bit, Python 3.12.15.

| Model | F1 mean (gate ≥ 0.80) | Schema-valid (gate ≥ 0.95) | Quantity accuracy | Invention rate (critical > 0.10) | Free RAM after (gate ≥ 3 GB) | Latency median / p95 (ms) | Status |
|---|---|---|---|---|---|---|---|
| llama3.2:3b | 0.8642 | 5/5 (1.00; 95% CI 0.57–1.00) | 26/27 (0.96; 95% CI 0.82–0.99) | 0/41 (0.00; 95% CI 0.00–0.09) | 2.12 | 4606 / 5759 | FAIL |
| qwen2.5:7b | 0.55 | 3/5 (0.60; 95% CI 0.23–0.88) | 13/15 (0.87; 95% CI 0.62–0.96) | 0/21 (0.00; 95% CI 0.00–0.15) | 2.11 | 11232 / 23832 | FAIL |
| qwen3:4b-instruct | 0.4 | 2/5 (0.40; 95% CI 0.12–0.77) | 12/13 (0.92; 95% CI 0.67–0.99) | 0/13 (0.00; 95% CI 0.00–0.23) | 2.42 | 15955 / 27421 | FAIL |
