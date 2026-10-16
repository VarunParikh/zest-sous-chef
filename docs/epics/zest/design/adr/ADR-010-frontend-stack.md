# ADR-010: Use React, Vite and Tailwind for the frontend
- **Status:** Accepted (owner approval, 2026-10-17)
- **Date:** 2026-10-17
- **Decision owner:** VJP (product owner); drafted by Claude
- **Authorisation:** Owner approved on 2026-10-17 ("Yes approved").

## Context
The UI is a split screen with a lever panel, chat, a mobile-shaped cart window and an inspector, built from DESIGN.md tokens.

## Decision drivers
- Fast build with Claude Code
- Maps cleanly to the design tokens
- Accessible component patterns (WCAG 2.1 AA)
- Testable with Playwright

## Options considered
| Option | Pros | Cons |
|---|---|---|
| React + Vite + Tailwind | Large ecosystem; fast dev server; utility classes fit tokens | Build toolchain |
| Plain HTML and JavaScript | No build step | Harder to keep chat, cart and lever state consistent |
| Next.js | Full-stack features | More than needed; server rendering not required |

## Decision
Use React with Vite, Tailwind CSS and **TypeScript** (approved by the owner on 2026-10-17, for typed API cards). State management (a small store or React context) is decided at build time and recorded in the CHANGELOG.

## Rationale
It is the quickest route to a polished, testable split-screen UI.

## Consequences
- **Positive:** Fast iteration; componentised UI.
- **Negative:** Node toolchain on the Mac; two dev servers.
- **Neutral:** None identified.

## Risks and mitigations
- Setup friction: one-command script
- Accessibility regressions: keyboard and focus tests (AC-32)

## Implementation and rollout
- `src/frontend` with Vite; proxy to the backend in dev

## Validation / rollback
Rollback: not planned; the REST contract keeps the backend independent.

## Related documents
DESIGN.md; PRD FR-100 to 104; NFR-03.
