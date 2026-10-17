# ADR-003 (v2): Local-first photo ingredient detection with a pluggable provider; Gemini optional; labelled sample photos as last fallback
- **Status:** Accepted, **amended 2026-10-17 (v2)** by owner decision: local-first, Gemini optional, pluggable. v1 (Gemini primary) is superseded; the original text is kept below under "v1 record". **Day-1 decision 2026-10-18 (owner approved): default `VISION_PROVIDER=samples`; photo accuracy NOT MET; Gemini 3.5 Flash-Lite available as an opt-in for demos only.**
- **Date:** 2026-10-17
- **Decision owner:** VJP (product owner); drafted by Claude
- **Authorisation:** Owner chose Gemini with user-uploaded photos and Constitution P9 was amended.

## v2 amendment (2026-10-17, owner decision)
**Owner instruction:** "Local first with Gemini as optional. Can be pluggable." Accuracy bar "70-80%; 8 out of 10 ingredients must be identified". Latency "10 to 20 secs with a progress bar".

**Decision.** Photo detection goes through a `VisionProvider` interface with three implementations: `ollama` (default if it passes the gate), `gemini` (optional; used only if a key is present and enabled), and `samples` (labelled sample photos with pre-computed results; always available). `VISION_PROVIDER` and `VISION_MODEL` are set in `.env`. The provider is chosen by the Day-1 benchmark (E3) using the rule below, not by preference.

**Candidates to benchmark (none verified on this hardware yet):** `qwen3-vl:4b` (3.3 GB download), `qwen3-vl:8b` (6.1 GB), a Gemma 4 vision tag (exact tag to be read from the Ollama library on the day), and Gemini Flash as the cloud reference. Llama 3.2 Vision is excluded on reported Ollama incompatibility (secondary source; re-check). Sizes: https://registry.ollama.ai/library/qwen3-vl.

**Selection rule (pre-registered in `eval/thresholds.yaml` v2, before any run).**
1. A candidate qualifies only if it meets the E3 gate: item precision >= 0.80 and item recall >= 0.70 on clear photos, and p95 latency <= 20 s on the M5 MacBook Air with the text model also loaded, and no out-of-memory or swap thrash in 3 repeated runs.
2. Owner target (not a gate): recall >= 0.80 (8 of 10 ingredients). Reported as met or not met.
3. Among qualifiers, the local default is the one with the highest recall; ties go to the smaller model.
4. If no local model qualifies: Gemini becomes the default only if a key is configured and it qualifies; otherwise the sample-photo path is the default and photo accuracy is reported as NOT MET. No claim of local vision accuracy is made.
5. The UI shows a progress bar while a photo is analysed. Detected items always go to a confirmation step before the cart changes (a wrong guess costs one tap, not a wrong order).

**Why.** Removes the key and network from the default demo path (demo-failure risk, R14), keeps photos on the device (Constitution P9 is satisfied by default; the consent notice applies only if Gemini is enabled), and allows one multimodal model to serve text and photos if memory is tight. **Costs.** Small vision models are weaker at fine-grained discrimination (DiningBench, ACL 2026), 6 GB for an 8B model sits beside the text model in 16 GB, and 11 photos give wide intervals, so a close result is INCONCLUSIVE rather than a pass.

**Dependencies.** No new Python package (`httpx` already calls Ollama). `google-genai` becomes optional. Pulling any vision model (several GB) needs the owner's go-ahead on the day (CLAUDE.md "ask before").

**Downstream documents** that still describe Gemini as primary are logged as conflict C15 and are overridden by this ADR until synced.

## Evidence and decision (Day 1, 2026-10-18)
Approved by the owner on 2026-10-18 ("Approve ADR-003: samples as the default (photo accuracy NOT MET), with Gemini Flash-Lite available as an opt-in for demos (option a)"). Evidence: `eval/results/E3-*.json`, [vision.md](../../verify/benchmarks/vision.md), [adr-proposals.md](../../verify/benchmarks/adr-proposals.md).

**Decision.** Default `VISION_PROVIDER=samples`: the bundled sample photos with pre-computed results, labelled as samples (FR-55). **Opt-in for demos (owner option a):** `VISION_PROVIDER=gemini` with `VISION_MODEL=gemini-3.5-flash-lite`, set by hand in the local `.env`, never the default. When it is on, the consent notice applies (FR-50, S-03, C8), detections are labelled as estimates and always confirmed before the cart changes, and photo accuracy is still reported as NOT MET. No local vision model is configured; the local `ollama` provider stays in code for a future re-run.

- **Decision (the pre-registered selection rule, applied as written):** no local model qualified, and Gemini did not qualify either. So the labelled sample-photo path is the default, and photo accuracy is reported as **NOT MET**. No claim of local or cloud vision accuracy is made.
- **Evidence (clear photos; gates: precision ≥ 0.80, recall ≥ 0.70, p95 ≤ 20 s, no failures, C29 memory checks):**

  | Candidate | Precision | Recall | p95 latency | Failures | Other |
  |---|---|---|---|---|---|
  | `gemini-3.5-flash-lite` (reference) | 159/207 = 0.77 (CI 0.71–0.82) | 159/252 = 0.63 (CI 0.57–0.69) | 3.5 s | 0/33 | Quality flags 30/33; flagged the dark photo RF10 as "ok" and listed 3–4 items on it in every run |
  | `qwen3-vl:4b-instruct` | 108/159 = 0.68 | 108/252 = 0.43 | 110 s | 6/33 (runaway JSON output) | About 1.1 GB swapped (71,575 swap-outs); text model stayed resident |
  | `gemma4:e2b-it-qat` | 31/70 = 0.44 | 31/252 = 0.12 | 51 s | 12/33 (schema errors) | |
  | `qwen3-vl:8b-instruct` | NOT RUN | | | | Owner decision: skipped for time and memory |

  `gemini-3.8-flash` was probed and not benchmarked: three calls took 23.5 s, 40 s and over 60 s, past the 20 s gate.
- **Closest candidate:** Gemini Flash-Lite. It is fast and reliable, and its precision interval reaches 0.80, but its recall interval lies wholly below 0.70. It did better on the demo photos (precision 0.87, recall 0.73) than on the test photos (0.70, 0.57).
- **Harness fix found while reviewing (before this proposal):** failed calls had been left out of recall, which flattered the failing models. The stored per-call rows were re-scored with failed calls counting as "found nothing" (Gemini unchanged; `qwen3-vl:4b` 0.65 → 0.43; `gemma4` 0.18 → 0.12). Raw model outputs are unchanged, each file says "RESCORED", and every verdict stays FAIL.
- **Caveats:**
  1. The labels are unverified and the pre-registered matching rule is strict. For example, a detection of "pepper" does not match a "red capsicum" label, and generic labels ("herbs", "bottles", "cut fruit in containers") rarely match anything. This likely understates every candidate. It was not changed after the results.
  2. 11 photos only, 4 of them development (demo) photos.
  3. On this 16 GB machine, memory pressure from the text model and guard makes local vision slow or swapping.
- **Consequences:** the photo flow (block 2.4) offers the bundled sample photos with pre-computed results, labelled as samples (FR-55). The demo can still show the full photo journey (consent notice, detections, confirmation step, cart) on those samples.

## Choices the owner may make instead (not a recommendation to override the rule)
- **(a) Opt-in Gemini Flash-Lite for demos:** `VISION_PROVIDER=gemini` set by hand, never the default. Detections are labelled as estimates and always confirmed before the cart changes; the consent notice applies (FR-50, S-03, C8); accuracy stays reported as NOT MET.
- **(b) Post-hoc improvement round:** the owner verifies the photo labels, then a re-run with an output-length cap for the local models (`qwen3-vl:4b`'s failures were runaway outputs). Results would be marked post-hoc.

## v1 record (superseded)

## Context
Photos of the user's ingredients must be analysed to list items with confidence. Small local vision models are weak on 16 GB; the owner chose a cloud model for photos only. Google's pricing page states free-tier content may be used to improve its products, which drove the P9 amendment.

## Decision drivers
- Detection quality on mixed Indian ingredients
- Privacy honesty (consent, EXIF stripping, deletion)
- Free to use
- Graceful fallback if unavailable

## Options considered
| Option | Pros | Cons |
|---|---|---|
| Gemini Flash or Flash-Lite (still image) | Strong accuracy, simple API, free tier | Cloud call; free-tier data use; rate limits; model names change |
| Local vision model via Ollama | Private, offline | Lower accuracy, memory-heavy next to the text model (dropped as fallback by owner) |
| Text-only confirmation (no vision) | Simplest | Fails the brief (photo entry method) |

## Decision
Use a standard Gemini Flash or Flash-Lite model for still images, configured in `.env`. If the call fails, times out or is rate-limited, offer bundled sample photos with pre-computed results, labelled as samples.

## Rationale
Accuracy matters for the photo flow to work; cloud use is limited to photos, with a consent notice, metadata stripping and no storage. The owner explicitly accepted the trade-off.

## Consequences
- **Positive:** Better detection than small local models; clear fallback.
- **Negative:** Photos leave the device; depends on a free tier whose limits and model names can change.
- **Neutral:** None identified.

## Risks and mitigations
- Free-tier data use: notice before first upload, testers told not to upload personal photos (P9)
- Rate limit during the demo: sample photos; avoid repeated live calls
- Key exposure: key only in a local git-ignored `.env`; owner advised to rotate the key that was pasted in chat (R14)

## Implementation and rollout
- `VISION_PROVIDER=gemini`, `VISION_MODEL` in config
- Schema-validated JSON of items and confidences
- Upload validation (FR-57), EXIF stripping (FR-51)

## Validation / rollback
Rollback: switch provider to the sample-photo path by config. Nothing is stored.

## Evidence to be measured on Day 1
| Measure | Method |
|---|---|
| Ingredient precision and recall | 15 sample photos (11 available on 2026-10-17) with hand labels |
| Latency | Per-call time including upload |
| Failure rate | Error and timeout count over repeated runs |
| Model name actually used | Recorded from the API listing on the day (not assumed) |
Results go in `verify/benchmarks/vision.md`.

## Related documents
Constitution P9; open-conflicts C8, C9; PRD FR-50 to 57; Platforms section 3.
