# ADR-001: Use Python 3.12 and FastAPI for the backend
- **Status:** Accepted (owner approval, 2026-10-17)
- **Date:** 2026-10-17
- **Decision owner:** VJP (product owner); drafted by Claude
- **Authorisation:** Owner approved on 2026-10-17 ("Yes approved"). Earlier: owner said "I am open to Python" (2026-10-16).

## Context
The backend orchestrates chat turns, retrieval, the recommendation engine, catalogue and cart, and calls Ollama and Gemini. It runs locally on a MacBook Air M5 (16 GB). The owner is new to the terminal and uses Claude Code to build.

## Decision drivers
- Best fit with local-AI and retrieval libraries (Chroma, embedding and BM25 libraries, Pydantic)
- Typed request and response schemas that double as the API contract
- Easy to test with pytest
- One-command local run on macOS
- Build effort within a 3-day window

## Options considered
| Option | Pros | Cons |
|---|---|---|
| Python + FastAPI | Strong AI ecosystem; Pydantic models shared with the Data Model; async support; auto-generated API docs | Another language to the frontend |
| Node/TypeScript (Express or Fastify) | One language across stack | Weaker fit for Chroma and Python-first retrieval tooling; duplicate type definitions |
| Flask | Simple | Less built-in validation and typing than FastAPI |

## Decision
Use Python 3.12 with FastAPI and Pydantic for the backend.

## Rationale
The data model, validators, generator, engine and evaluation scripts are all Python; keeping one language removes a translation layer and speeds up Claude Code-assisted development. This is a qualitative decision; no benchmark would change it.

## Consequences
- **Positive:** One language for engine, data generation, tests and evaluation; schemas defined once.
- **Negative:** Requires a Python environment on the owner's Mac; the frontend is a separate toolchain.
- **Neutral:** None identified.

## Risks and mitigations
- Version drift: pin dependencies in a lock file
- Setup friction for a terminal beginner: a one-command setup script and a README guide

## Implementation and rollout
- `pyproject.toml` with pinned versions
- `scripts/serve` starts uvicorn
- Pydantic models from the Data Model section 14

## Validation / rollback
Validated by a working health endpoint and the acceptance suite. Rollback: replace the API layer only; engine and cart are framework-independent modules.

## Related documents
Architecture section 3; Platforms section 1; Data Model section 14.
