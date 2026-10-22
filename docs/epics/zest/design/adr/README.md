# Architecture Decision Records: Zest AI Sous-Chef

Format follows the `write-adr` skill. An ADR is marked **Accepted** only where the owner has decided. "Proposed" means either awaiting owner approval or awaiting Day-1 evidence. Evidence is produced by scripts in the repo, so a reviewer can re-run it.

| ADR | Decision | Status | Evidence |
|---|---|---|---|
| [001](ADR-001-backend-framework.md) | Python 3.12 and FastAPI | Accepted (owner, 2026-10-17) | Qualitative |
| [002](ADR-002-text-model.md) | Local text model: `llama3.2:3b`, 4k context | **Accepted (owner, 2026-10-18)** from E1 | `verify/benchmarks/text-models.md` |
| [003](ADR-003-vision-approach.md) | Pluggable photo detection; v3: local `qwen3-vl:4b-instruct` by default (failed E3, owner decision), Gemini 3.5 Flash-Lite opt-in, samples for the demo and as fallback; photo accuracy NOT MET | **Accepted v3 (owner decision 2026-10-18, C37; re-approved the same day)** | `verify/benchmarks/vision.md` |
| [004](ADR-004-retrieval-approach.md) | Hybrid BM25 + vector with RRF; v3 (C45): open requests use a course-wide lever-ranked pool and no dish repeats in a session; v2: add-on suggestions from curated pairs plus vector neighbours (weighted RRF, course rule) | Accepted; v2 amended 2026-10-17; Day-1 evidence recorded 2026-10-18 (hybrid default, k = 60, add-ons 2:1) | `verify/benchmarks/retrieval.md` |
| [005](ADR-005-vector-store-and-embedder.md) | Embedded Chroma with the default all-MiniLM-L6-v2 embedder | **Accepted (owner, 2026-10-18)** from E5 | `verify/benchmarks/retrieval.md` |
| [006](ADR-006-guard-design.md) | Input guard: rules plus `llama-guard3:1b`; v3 ignores the S8 (Intellectual Property) and S6 (Specialized Advice) categories | **Accepted v3 (owner decisions 2026-10-18, C40, C44)**; v1 accepted from E4 | `verify/benchmarks/guard.md` |
| [007](ADR-007-state-and-storage.md) | In-memory state, JSON catalogue | Accepted | Qualitative |
| [008](ADR-008-variant-scoring.md) | Lever scores plus price value term | Accepted; constants to be tuned | `verify/benchmarks/variant-scoring.md` |
| [009](ADR-009-no-mcp-plain-rest.md) | Plain REST, no MCP | Accepted | Qualitative |
| [010](ADR-010-frontend-stack.md) | React, Vite, Tailwind | Accepted (owner, 2026-10-17) | Qualitative |
| [011](ADR-011-macos-app-packaging.md) | Self-contained `Zest.app` in a DMG: bundled Python 3.12 and Ollama 0.40.5, models fetched on first launch, unsigned | Accepted in part (owner decisions D1 to D3, 2026-10-22); text awaits owner review | T-111 to T-115 |
| [012](ADR-012-zest-2-side-by-side.md) | Zest 2.0 next to 1.0: ports 8100/5273, own data folder, private Ollama 11436, shared model folder, badged icon | Accepted (owner, 2026-10-22, with the Zest 2.0 plan) | T-127, T-128 |

Dependencies awaiting approval under Constitution G3 at install time: a BM25 library (approved in principle for ADR-004), Chroma, Pydantic, FastAPI, pytest, Playwright.
