# Block 1.5 plan: Day-1 decision evidence (E1, E3, E4, E5)

Status: working plan (not a spec), 2026-10-18. Specs: Evaluation Plan §4 and §6, `eval/thresholds.yaml` v3, ADR-002 to ADR-006. **Nothing here has been run.** Every evaluation is NOT RUN until its results file exists.

## Machine (read 2026-10-18)
Apple M5, 16 GB RAM (about 5.5 GB free or inactive at idle with the IDE open), 790 GB disk free, Ollama 0.40.5. Already installed: `llama3.2:3b` (2.0 GB), `qwen2.5:7b` (4.7 GB).

## Candidates and downloads (tags and sizes read from ollama.com today; re-read at pull time)
| Evaluation | Candidate | Download | Status |
|---|---|---|---|
| E1 text (ADR-002) | `llama3.2:3b` | none | installed |
| E1 text | `qwen2.5:7b` | none | installed |
| E1 text | `qwen3:4b-instruct` | 2.5 GB | needs approval |
| E1 text and E3 vision | `gemma4:e2b-it-qat` (one model for text and photos, ADR-003 "if memory is tight") | 4.3 GB | needs approval |
| E3 vision (ADR-003 v2) | `qwen3-vl:4b-instruct` | 3.3 GB | needs approval |
| E3 vision | `qwen3-vl:8b-instruct` | 6.1 GB | needs approval; tight beside a text model in 16 GB, which the "no swap thrash" gate tests |
| E3 vision | Gemini Flash (reference) | none | runs only if a key is in the local `.env`; otherwise NOT RUN |
| E4 guard (ADR-006) | rules only | none | — |
| E4 guard | rules plus `llama-guard3:1b` | 1.6 GB | needs approval |
| E5 retrieval (ADR-005) | Chroma default all-MiniLM-L6-v2 | none | installed (block 1.4) |
| E5 retrieval | Ollama embedder `nomic-embed-text` | about 0.3 GB (verify) | needs approval |
Total new downloads if all approved: about 18 GB.

## Code to build first (test-first, no downloads)
1. **Eval harness** `eval/runner.py`: one result schema (Evaluation Plan §6: id, system, dataset version and hash, environment, k/n with Wilson 95% intervals, critical failures, per-example rows, status), environment capture (commit, models and digests from `ollama show`, embedder, library versions, seeds), thresholds read with `yaml.safe_load`. `make eval-decisions`.
2. **E5** `scripts/benchmark/retrieval.py`: lexical, vector and hybrid with k = 20, 60, 100, recall@5, recall@pool, MRR per query type, and the critical "pool omits an eligible exact-name match". Index time and query latency at 1,000 and 5,000 variants. Add-on arm: curated only, vector only, and fused at 1:1, 2:1, 3:1; curated-pair recovery in the top 5, coverage for dishes with no pair, persona check. No model download is needed for the default embedder.
3. **LLM client** `backend/llm`: Ollama over `httpx`, temperature 0, NFR-10 timeouts, one retry, Pydantic schema validation (Agent Design §5, §8). Prompt file `recipe_extract` v1 (Agent Design §6.2). **E1** `scripts/benchmark/text_models.py`: F1 after synonym resolution, quantity accuracy, schema-valid rate, invention rate (critical over 10%), TTFT and latency, memory from `ollama ps`.
4. **Guard rules** `backend/guard.screen()` (ADR-006, Agent Design §7), built with its own tests. **E4** `scripts/benchmark/guard.py`: block rate and false positives for rules only and rules plus the classifier.
5. **Vision provider** `backend/llm/vision` (`ollama`, `gemini`, `samples`) and prompt `photo_detect` v1. **E3** `scripts/benchmark/vision.py`: precision and recall on clear photos, calibration, p95 latency with the text model loaded, 3 repeated runs, swap check (`vm_stat`, `memory_pressure`; no new dependency).

## Order
E5 (no download) → E4 rules only → E1 (one 2.5 GB pull) → E4 classifier → E3 (largest pulls, last). Each step writes `eval/results/{id}.json` and `verify/benchmarks/{retrieval,text-models,guard,vision}.md`, then updates its ADR status. A missed gate stops the block for an owner decision (build plan §8).

## Labels the owner reviews before the run (Evaluation Plan §5, §8)
`retrieval_v1` (61 queries), `recipes_v1` (10), and the 11 photo label sets in `mock-data/photos.json`, which are still marked DRAFT ground truth. Runs on unreviewed labels would be reported as such.

## Owner decisions (2026-10-18)
1. **Downloads staged:** first `qwen3:4b-instruct`, `llama-guard3:1b`, `nomic-embed-text` (about 4.4 GB), each confirmed again just before its pull. Vision candidates wait until E1, E4 and E5 have results.
2. **Gemini arm runs** in E3: the owner adds a fresh key to the local `.env` (never in chat, code or commits). The arm is NOT RUN until the key is there.
3. **Labels reviewed first:** the harness and the E5, E4 and E1 code are built and smoke-checked on the dev split only (output discarded, nothing recorded), then work stops until the owner has reviewed `retrieval_v1`, `recipes_v1` and the photo labels.
