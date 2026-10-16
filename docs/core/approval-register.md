# Approval Register

Purpose: one place that records which documents the owner has approved, and when. Only the owner approves (Authority Matrix 3.2). Claude changes a document's header from "DRAFT" to "Approved" only after the owner says so, and records it here and in the CHANGELOG.

Why it matters: `CLAUDE.md` tells Claude Code not to implement anything that lacks an approved spec section. Until the build-gating documents are approved, Claude Code is meant to stop.

## How to approve (approve by exception)
Reply with one of:
- "Approve all" (Claude flips every Tier A, B and C document below).
- "Approve all except: <document names>" plus what to change in those.
- Or approve by tier, for example "Approve Tier A and B; hold Tier C".
Approving a document means: you have read it or the parts you care about, you accept its decisions, and later changes will go through an amendment with a CHANGELOG entry.

## Reading priority
- **Tier A, read before approving (they define what gets built):** PRD, Data Model, Architecture, API Spec, Agent Design, Build Plan.
- **Tier B, skim for decisions you must own:** User Stories, Conversation Design (voice already agreed), Security and Privacy Note, Test Plan, Evaluation Plan (especially its thresholds), ADR index.
- **Tier C, reference, rarely contentious:** Constitution, Strategy, Platforms, References and Glossary, BRD, Personas, Product Research, Risk Register, Mock Data Plan.

## Register
| Doc | Path | Version | Tier | Status | Approved by / date |
|---|---|---|---|---|---|
| Product spec (PRD) | `docs/epics/zest/requirements/product-spec.md` | v0.3 | A | Draft | |
| Data Model | `docs/epics/zest/design/data-model.md` | v0.1 | A | Draft | |
| Architecture | `docs/epics/zest/design/architecture.md` | v0.1 | A | Draft | |
| API Spec | `docs/epics/zest/design/api-spec.md` | v0.1 | A | Draft | |
| Agent Design | `docs/epics/zest/design/agent-design.md` | v0.1 | A | Draft | |
| Build Plan | `docs/epics/zest/build-plan.md` | v0.1 | A | Draft | |
| User Stories and Traceability | `docs/epics/zest/requirements/user-stories.md` | v0.2 | B | Draft | |
| Conversation Design | `docs/epics/zest/design/conversation-design.md` | v0.1 | B | Draft (voice agreed 2026-10-17) | |
| Security and Privacy Note | `docs/epics/zest/design/security-privacy-note.md` | v0.1 | B | Draft | |
| Test Plan | `docs/epics/zest/verify/test-plan.md` | v0.1 | B | Draft (lean set agreed) | |
| Evaluation Plan | `docs/epics/zest/verify/evaluation-plan.md` | v0.1 | B | Draft (thresholds unapproved) | |
| ADR-001 Backend framework | `design/adr/ADR-001-...` | | B | **Accepted** | Owner, 2026-10-17 |
| ADR-003 Vision approach | `design/adr/ADR-003-...` | | B | **Accepted** (accuracy measured Day 1) | Owner, 2026-10-16/17 |
| ADR-004 Retrieval approach | `design/adr/ADR-004-...` | | B | **Accepted** (benchmark gate Day 1) | Owner, 2026-10-17 |
| ADR-005 Vector store | `design/adr/ADR-005-...` | | B | **Accepted** for the store; embedder open | Owner, 2026-10-17 |
| ADR-007 State and storage | `design/adr/ADR-007-...` | | B | **Accepted** | Owner brief |
| ADR-008 Variant scoring | `design/adr/ADR-008-...` | | B | **Accepted** (constants tuned) | Owner, 2026-10-17 |
| ADR-009 No MCP | `design/adr/ADR-009-...` | | B | **Accepted** | Owner, 2026-10-17 |
| ADR-010 Frontend stack | `design/adr/ADR-010-...` | | B | **Accepted** (with TypeScript) | Owner, 2026-10-17 |
| ADR-002 Text model | `design/adr/ADR-002-...` | | B | Proposed: decided by Day-1 benchmark | |
| ADR-006 Guard design | `design/adr/ADR-006-...` | | B | Proposed: decided by Day-1 benchmark | |
| Constitution | `docs/core/constitution.md` | v0.2 | C | Draft | |
| Product Strategy | `docs/core/product-strategy.md` | v0.1 | C | Draft | |
| Product Platforms | `docs/core/product-platforms.md` | v0.1 | C | Draft | |
| References and Glossary | `docs/core/references-and-glossary.md` | v0.1 | C | Draft | |
| BRD | `docs/epics/zest/requirements/business-requirements.md` | v0.1 | C | Draft (has its own approval table) | |
| Personas | `docs/epics/zest/discovery/personas.md` | v0.1 | C | Draft | |
| Product Research | `docs/epics/zest/discovery/product-research.md` | v0.1 | C | Draft | |
| Assumptions and Risk Register | `docs/epics/zest/discovery/assumptions-and-risk-register.md` | v0.1 | C | Living document, versioned, not approved once | |
| Mock Data Plan | `docs/epics/zest/design/mock-data-plan.md` | v0.1 | C | Draft | |

## Items that need an explicit owner answer (not just approval)
| Item | Where | Default if you say "go" |
|---|---|---|
| Conflicts still marked "Proposed" (C1, C2, C3, C5, C6, C7, C9, C10, C14) | `docs/core/open-conflicts.md` | Follow the proposed resolution in each row |
| Open questions OQ-8, OQ-9, OQ-10 (kept at defaults), OQ-13 constants | PRD section 15 | Accept defaults; tune β0 in testing |
| Evaluation thresholds and ADR gates (all my proposals) | Evaluation Plan section 4; ADR-002, 003, 006 | Accept as proposed and commit `eval/thresholds.yaml` before the first run |
| Repository licence | Not yet chosen | Choose before first push |
| Real demo YouTube links (3 to 4) and phone photos | Mock Data Plan, Test Plan | Owner supplies |

## Rules
1. Approving does not freeze a document; it baselines it. Later edits are amendments with a version bump, a CHANGELOG entry and a note here.
2. A document that is edited after approval returns to "Draft (amended)" until re-approved if the change affects a requirement, a guardrail or a decision.
3. Living documents (Risk Register, CHANGELOG, open-conflicts) are versioned, not approved once.
