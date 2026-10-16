# ADR-009: Use plain REST and no MCP server at runtime
- **Status:** Accepted (owner decision, 2026-10-17)
- **Date:** 2026-10-17
- **Decision owner:** VJP (product owner); drafted by Claude
- **Authorisation:** Owner: no need for an MCP server.

## Context
The question was whether to expose the mock store through the Model Context Protocol so the model could call it as tools.

## Decision drivers
- 3-day deadline
- Model must not have direct authority over the cart or prices (P3)
- Mock data only
- Simplicity

## Options considered
| Option | Pros | Cons |
|---|---|---|
| Plain REST between frontend and backend; code calls the catalogue directly | Simple; the model has no tool authority | No standard tool interface |
| REST plus an MCP server over the mock store | Demonstrates a standard protocol | Extra surface; lets a model call tools; no benefit for mock data |

## Decision
Use plain REST only. The model returns structured JSON that code validates; it does not call the catalogue or cart.

## Rationale
Authority stays in code, which is what the Constitution requires, and scope stays small.

## Consequences
- **Positive:** Smaller attack surface; less to build and test.
- **Negative:** No MCP showcase; the reviewer may ask. The answer is this record.
- **Neutral:** None identified.

## Risks and mitigations
- Reviewer interest in MCP: the Decision Evidence Log states the reasoning; MCP is listed as possible future scope

## Implementation and rollout
- No MCP dependencies

## Validation / rollback
Revisit only if a later scope needs external agent access.

## Related documents
Constitution P3 and Authority Matrix; Risk Register decision log.
