# Architecture Decision Records: Zest AI Sous-Chef

Format follows the `write-adr` skill. An ADR is marked **Accepted** only where the owner has decided. "Proposed" means either awaiting owner approval or awaiting Day-1 evidence. Evidence is produced by scripts in the repo, so a reviewer can re-run it.

| ADR | Decision | Status | Evidence |
|---|---|---|---|
| [001](ADR-001-backend-framework.md) | Python 3.12 and FastAPI | Accepted (owner, 2026-10-17) | Qualitative |
| [002](ADR-002-text-model.md) | Local text model | **Proposed: to be measured Day 1** | `verify/benchmarks/text-models.md` |
| [003](ADR-003-vision-approach.md) | Gemini free tier for photos, sample-photo fallback | Accepted; accuracy to be measured Day 1 | `verify/benchmarks/vision.md` |
| [004](ADR-004-retrieval-approach.md) | Hybrid BM25 + vector with RRF | Accepted; benchmark gate Day 1 | `verify/benchmarks/retrieval.md` |
| [005](ADR-005-vector-store-and-embedder.md) | Embedded Chroma; embedder open | Store accepted; **embedder to be measured Day 1** | `verify/benchmarks/retrieval.md` |
| [006](ADR-006-guard-design.md) | Input guard design | **Proposed: to be measured Day 1** | `verify/benchmarks/guard.md` |
| [007](ADR-007-state-and-storage.md) | In-memory state, JSON catalogue | Accepted | Qualitative |
| [008](ADR-008-variant-scoring.md) | Lever scores plus price value term | Accepted; constants to be tuned | `verify/benchmarks/variant-scoring.md` |
| [009](ADR-009-no-mcp-plain-rest.md) | Plain REST, no MCP | Accepted | Qualitative |
| [010](ADR-010-frontend-stack.md) | React, Vite, Tailwind | Accepted (owner, 2026-10-17) | Qualitative |

Dependencies awaiting approval under Constitution G3 at install time: a BM25 library (approved in principle for ADR-004), Chroma, Pydantic, FastAPI, pytest, Playwright.
