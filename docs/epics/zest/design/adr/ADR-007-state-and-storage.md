# ADR-007: Keep session state in memory and the catalogue in JSON files loaded at startup
- **Status:** Accepted (the brief and DESIGN.md say a refresh resets everything; owner confirmed no persistence)
- **Date:** 2026-10-17
- **Decision owner:** VJP (product owner); drafted by Claude
- **Authorisation:** Owner brief: refresh resets; mock data only.

## Context
The prototype has no accounts. The cart, chat and levers must reset on refresh, and the catalogue is mock data owned by the project.

## Decision drivers
- Simplicity and reproducibility
- Matches the product rule (refresh resets)
- No personal data stored (P9)
- Fast tests

## Options considered
| Option | Pros | Cons |
|---|---|---|
| In-memory sessions + JSON files | Simplest; deterministic | Lost on restart (intended) |
| SQLite for everything | Familiar, queryable | More code; persistence not wanted for session data |
| Redis or server database | Scalable | Overkill and against the one-command goal |

## Decision
Hold sessions in memory in the backend. Load catalogue, recipes, synonyms and trends from JSON/CSV files into memory at startup. Chroma is the only persistent store, rebuilt from the files.

## Rationale
It meets the product rule and keeps the system simple and testable. SQLite remains an option for the catalogue if lookup speed at 5,000 variants requires it.

## Consequences
- **Positive:** Simple, fast, no personal data at rest.
- **Negative:** No multi-user persistence; state lost on restart.
- **Neutral:** None identified.

## Risks and mitigations
- Restart loses a demo session: warm start script and health page
- Memory growth: bounded by a few sessions

## Implementation and rollout
- Session store class with a lock per session
- Catalogue loader with validation (V1 to V14)

## Validation / rollback
Rollback: introduce SQLite behind the catalogue interface if needed.

## Related documents
PRD NFR-04; Data Model section 2; DESIGN.md.
