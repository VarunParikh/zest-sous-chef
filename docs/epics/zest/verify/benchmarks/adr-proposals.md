# Proposed ADR updates from the Day-1 evidence (awaiting owner approval)

Status: **PROPOSED, 2026-10-18.** Nothing here changes an ADR until the owner approves it. On approval, each block below goes into its ADR as an "Evidence and decision (Day 1)" section, the ADR's status line changes as stated, and the change goes in the Approval Register and the CHANGELOG.
Evidence: `eval/results/*.json` (test split; commits `28a69da`, `4b3ae25`) and `eval/results/post-hoc/E1-llama3.2_3b.json` (commit `782db12`), summarised in [retrieval.md](retrieval.md), [guard.md](guard.md) and [text-models.md](text-models.md). These are small samples: every rate is quoted as k/n with its 95% Wilson interval, and passes whose interval straddles the gate are marked "not separable" (C28).

## ADR-002 Text model: Proposed → **Accepted: `llama3.2:3b` with a 4,096-token context**
- **Decision:** `LLM_MODEL=llama3.2:3b`, `LLM_NUM_CTX=4096`.
- **Evidence (E1, test split, 5 recipes):**
  - First run, Ollama's default 16k context: no candidate passed.
    - `llama3.2:3b` met F1 (0.86), schema validity (5/5) and invention (0/41), but free RAM after was 2.12 GB against the 3 GB gate.
    - `qwen2.5:7b` failed: F1 0.55, valid JSON 3/5.
    - `qwen3:4b-instruct` failed: F1 0.40, valid JSON 2/5. Both Qwen models failed validation on the Hinglish and transcript rows.
  - Post-hoc rerun (owner decision): `llama3.2:3b` at 4k context, other apps closed. **All gates pass:**
    - F1 0.86; schema 5/5 (95% CI 0.57–1.00, not separable).
    - Quantities 26/27; invention 0/41.
    - Free RAM after 6.7 GB; latency median 4.2 s, p95 5.4 s.
- **Caveats:**
  1. Two things changed in the rerun, a smaller window and closed apps. With 4k, Ollama held the model at 2.6 GB instead of 4.0 GB; free RAM before loading also rose from 5.4 GB to 7.9 GB.
  2. n = 5, so every interval is wide.
  3. Hinglish rows scored lower (F1 0.71 to 0.91).
  4. Live YouTube transcripts can exceed 4k tokens, so the video flow must cap the transcript length it sends (block 2.4).
- **Latency target (E1 says to record it here):** the extraction call is about 4–5 s (p95 5.4 s). E11 sets the end-to-end targets per flow.
- **Demo rule:** close other apps before the demo (Test Plan §9). The warm-up script loads `llama3.2:3b` at 4k.

## ADR-004 Retrieval: Accepted v2 → **Accepted v2, evidence recorded; hybrid stays the default, k = 60, add-on weights 2:1**
- **Evidence (E5, 30 test queries):**
  - Hybrid found a relevant item in the pool for 30/30 queries, lexical for 28/30. On the mood subset: hybrid 7/7, lexical 5/7.
  - The pre-registered rule is met: at least as good overall, and better on moods. Not separable at n = 7 moods.
  - No critical failure: no pool omitted an exact-name match.
  - k = 20, 60 and 100 gave identical results, so `RRF_K` stays 60.
  - Latency at 5,135 variants: query median about 12 ms, p95 about 20 ms. Index build about 54 s.
- **Add-on arm:**
  - Fused 2:1 passes both gates: curated pairs in the top 5, 108/127 (0.85); dishes with no pair covered, 101/101. 0 persona breaks.
  - 3:1 gives the same; 1:1 fails curated recovery (88/127).
  - Curated only covers 0/101 dishes that have no pair, and vector only recovers 16/127 curated pairs.
  - The ADR-004 v2 rule ("if the vector arm adds no eligible add-on for no-pair dishes, the owner decides") does not trigger: the vector arm covers all of them.
  - **Keep `ADDON_WEIGHTS=curated:2,vector:1`.**
  - Course rule: 1937/2580 (0.75) of raw vector neighbours are companion courses. The rule removes the rest, as designed.

## ADR-005 Vector store and embedder: Accepted (store) / Proposed (embedder) → **Accepted: Chroma with its default all-MiniLM-L6-v2 embedder**
- **Evidence (E5):** the default embedder and `nomic-embed-text` (Ollama) tied on recall within the pool in every subset (30/30 in hybrid).
  - nomic was slightly better on the vector-only mood top 5 (7/7 vs 5/7) and on hybrid MRR (0.89 vs 0.88).
  - Index build at 5,135 variants: 54 s (MiniLM) vs 62 s (nomic). Query p95 was about 20 ms for both.
- **Why the default:** it runs inside the backend process with no extra Ollama model (nomic is resident at 335 MB beside the text model and Llama Guard). It was already downloaded once into the git-ignored `data/models/`, and it showed no measured quality loss on this set.
  - nomic was run without its recommended task prefixes, which may understate it. It stays available through `EMBEDDING_PROVIDER=ollama`.
- **Regional names:** kothmir, kandha, batata and the other regional test queries resolved in every hybrid system. The misspelling "paner" did not resolve (spot check in block 1.4). That is a known limitation.
- **Bug found and fixed during E5:** an interrupted index build had been treated as current (fixed in `28a69da`; that run was discarded).

## ADR-006 Guard: Proposed → **Accepted: rules plus `llama-guard3:1b`**
- **Evidence (E4, 20 test prompts):**
  - Rules alone: **FAIL**, 9/13 attacks blocked (0.69 against the 0.90 gate). They missed both transcript injections, one direct injection and one hazard.
  - Rules plus `llama-guard3:1b`: **PASS**, 12/13 blocked (0.92; CI 0.67–0.99, not separable), 0/7 false positives.
  - Cost: 1.7 GB resident; classifier call median 53 ms, p95 133 ms. The first cold call took 6.6 s, so the warm-up script must load it.
- **Design:** rules run first (free, deterministic); the classifier runs only when the rules pass the text. Fetched text still goes through spotlighting and the no-authority design, whatever the guard says.
- **Caveats:**
  1. The rules author saw test items G02 and G04 while checking the file format. This is disclosed in every E4 result; the rules were not tuned on the test split.
  2. One injection (G08) passed both arms.
  3. English only.
  4. The end-to-end critical check (an injection must never change the cart) runs with the E9 harness in block 2.
- **Memory budget with all three models resident:** text 2.6 GB + guard 1.7 GB + (optional) nomic 0.3 GB. The vision model chosen in E3 must fit beside these; E3's "no swap" gate tests that.

## Not yet decided here
- **ADR-003 vision:** E3 has not run. The vision downloads (about 13.7 GB) wait for owner approval. The Gemini key is set in `.env` but is 53 characters, not the usual 39-character `AIza…` format; the owner should check it before E3.
