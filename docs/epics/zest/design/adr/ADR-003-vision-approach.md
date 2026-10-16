# ADR-003: Use the Gemini API free tier for photo ingredient detection, with labelled sample photos as fallback
- **Status:** Accepted (owner decision, conflicts C8 and C9, 2026-10-16 and 2026-10-17); model name and accuracy to be measured Day 1
- **Date:** 2026-10-17
- **Decision owner:** VJP (product owner); drafted by Claude
- **Authorisation:** Owner chose Gemini with user-uploaded photos and Constitution P9 was amended.

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
| Ingredient precision and recall | 15 sample photos with hand labels |
| Latency | Per-call time including upload |
| Failure rate | Error and timeout count over repeated runs |
| Model name actually used | Recorded from the API listing on the day (not assumed) |
Results go in `verify/benchmarks/vision.md`.

## Related documents
Constitution P9; open-conflicts C8, C9; PRD FR-50 to 57; Platforms section 3.
