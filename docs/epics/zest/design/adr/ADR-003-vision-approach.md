# ADR-003 (v2): Local-first photo ingredient detection with a pluggable provider; Gemini optional; labelled sample photos as last fallback
- **Status:** Accepted, **amended 2026-10-17 (v2)** by owner decision: local-first, Gemini optional, pluggable. v1 (Gemini primary) is superseded; the original text is kept below under "v1 record". Local model choice is decided by the Day-1 benchmark, so the model name is still open.
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
