# Approval Register

**2026-10-17: owner replied "Approve all" (all tiers). ADR-002 and ADR-006 stay Proposed by design (decided by the Day-1 benchmark). Proposed conflicts C1, C2, C3, C5, C6, C7, C9, C10, C14, the evaluation thresholds and the OQ defaults were accepted as written.**

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
| Product spec (PRD) | `docs/epics/zest/requirements/product-spec.md` | v0.4 | A | **Approved** (ADR-004 v2 sync, C16) | Owner, 2026-10-17 (re-approved after ADR-004 v2 sync) |
| Data Model | `docs/epics/zest/design/data-model.md` | v0.2 | A | **Approved** (ADR-004 v2 sync, C16) | Owner, 2026-10-17 (re-approved after ADR-004 v2 sync) |
| Architecture | `docs/epics/zest/design/architecture.md` | v0.2 | A | **Approved** (ADR-004 v2 sync, C16) | Owner, 2026-10-17 (re-approved after ADR-004 v2 sync) |
| API Spec | `docs/epics/zest/design/api-spec.md` | v0.1 | A | **Approved** | Owner, 2026-10-17 |
| Agent Design | `docs/epics/zest/design/agent-design.md` | v0.1 | A | **Approved** | Owner, 2026-10-17 |
| Build Plan | `docs/epics/zest/build-plan.md` | v0.2 | A | **Approved** (ADR-004 v2 sync, C16) | Owner, 2026-10-17 (re-approved after ADR-004 v2 sync) |
| User Stories and Traceability | `docs/epics/zest/requirements/user-stories.md` | v0.3 | B | **Approved** (ADR-004 v2 sync, C16) | Owner, 2026-10-17 (re-approved after ADR-004 v2 sync) |
| Conversation Design | `docs/epics/zest/design/conversation-design.md` | v0.1 | B | **Approved** (voice agreed 2026-10-17) | Owner, 2026-10-17 |
| Security and Privacy Note | `docs/epics/zest/design/security-privacy-note.md` | v0.1 | B | **Approved** | Owner, 2026-10-17 |
| Test Plan | `docs/epics/zest/verify/test-plan.md` | v0.2 | B | **Approved** (ADR-004 v2 sync, C16); `verify/test-cases.md` approved with it | Owner, 2026-10-17 (re-approved after ADR-004 v2 sync) |
| Evaluation Plan | `docs/epics/zest/verify/evaluation-plan.md` | v0.2 | B | **Approved** (ADR-004 v2 sync, C16); thresholds v3 approved as proposed | Owner, 2026-10-17 (re-approved after ADR-004 v2 sync) |
| ADR-001 Backend framework | `design/adr/ADR-001-...` | | B | **Accepted** | Owner, 2026-10-17 |
| ADR-003 Vision approach | `design/adr/ADR-003-...` | v2 | B | **Accepted, amended v2** (local-first, pluggable; provider chosen by Day-1 E3) | Owner, 2026-10-17 |
| ADR-004 Retrieval approach | `design/adr/ADR-004-...` | v2 | B | **Accepted, amended v2** (add-on suggestions: curated pairs plus vector neighbours; benchmark gate Day 1) | Owner, 2026-10-17 |
| ADR-005 Vector store | `design/adr/ADR-005-...` | | B | **Accepted** for the store; embedder open | Owner, 2026-10-17 |
| ADR-007 State and storage | `design/adr/ADR-007-...` | | B | **Accepted** | Owner brief |
| ADR-008 Variant scoring | `design/adr/ADR-008-...` | | B | **Accepted** (constants tuned) | Owner, 2026-10-17 |
| ADR-009 No MCP | `design/adr/ADR-009-...` | | B | **Accepted** | Owner, 2026-10-17 |
| ADR-010 Frontend stack | `design/adr/ADR-010-...` | | B | **Accepted** (with TypeScript) | Owner, 2026-10-17 |
| ADR-002 Text model | `design/adr/ADR-002-...` | | B | Proposed: decided by Day-1 benchmark | |
| ADR-006 Guard design | `design/adr/ADR-006-...` | | B | Proposed: decided by Day-1 benchmark | |
| Constitution | `docs/core/constitution.md` | v0.2 | C | **Approved** | Owner, 2026-10-17 |
| Product Strategy | `docs/core/product-strategy.md` | v0.1 | C | **Approved** | Owner, 2026-10-17 |
| Product Platforms | `docs/core/product-platforms.md` | v0.1 | C | **Approved** | Owner, 2026-10-17 |
| References and Glossary | `docs/core/references-and-glossary.md` | v0.1 | C | **Approved** | Owner, 2026-10-17 |
| BRD | `docs/epics/zest/requirements/business-requirements.md` | v0.1 | C | **Approved** (has its own approval table) | Owner, 2026-10-17 |
| Personas | `docs/epics/zest/discovery/personas.md` | v0.1 | C | **Approved** | Owner, 2026-10-17 |
| Product Research | `docs/epics/zest/discovery/product-research.md` | v0.1 | C | **Approved** | Owner, 2026-10-17 |
| Assumptions and Risk Register | `docs/epics/zest/discovery/assumptions-and-risk-register.md` | v0.1 | C | **Approved** as baseline v0.1; stays a living document | Owner, 2026-10-17 |
| Mock Data Plan | `docs/epics/zest/design/mock-data-plan.md` | v0.2 | C | **Approved** (ADR-004 v2 sync, C16) | Owner, 2026-10-17 (re-approved after ADR-004 v2 sync) |

## Items that need an explicit owner answer (not just approval)
| Item | Where | Default if you say "go" |
|---|---|---|
| Conflicts still marked "Proposed" (C1, C2, C3, C5, C6, C7, C9, C10, C14) | `docs/core/open-conflicts.md` | Follow the proposed resolution in each row |
| Open questions OQ-8, OQ-9, OQ-10 (kept at defaults), OQ-13 constants | PRD section 15 | Accept defaults; tune β0 in testing |
| Evaluation thresholds and ADR gates (all my proposals) | Evaluation Plan section 4; ADR-002, 003, 006 | Accept as proposed and commit `eval/thresholds.yaml` before the first run |
| Repository licence | **Decided 2026-10-17: MIT** (owner delegated the choice) | Done |
| Demo YouTube links and photos | Supplied 2026-10-17; see `mock-data/videos.json` and `mock-data/photos.json` | Photo provenance problem open (see photos.json) |

## Rules
1. Approving does not freeze a document; it baselines it. Later edits are amendments with a version bump, a CHANGELOG entry and a note here.
2. A document that is edited after approval returns to "Draft (amended)" until re-approved if the change affects a requirement, a guardrail or a decision.
3. Living documents (Risk Register, CHANGELOG, open-conflicts) are versioned, not approved once.

## Decisions log (after approval)
| Date | Decision | Where recorded |
|---|---|---|
| 2026-10-17 | Off-topic prompts are blocked with a polite templated reply; this defines "blocked" in E4 (one-line clarification to the Evaluation Plan, which stays Approved) | `evaluation-plan.md` E4, `eval/thresholds.yaml`, `eval/datasets/README.md` |
| 2026-10-17 | Claude Code surface for the build: desktop app, Code tab (owner has a Claude Pro plan) | `day-0-walkthrough.md` |
| 2026-10-17 | Evaluation label sample (20 rows) reviewed and approved by the owner; per-row verdicts not recorded | `eval/datasets/README.md` |
| 2026-10-17 | Doc-sync review against the seed data (same assistant, not independent): 7 documents annotated with current counts, paths and decisions; mock-data-plan dish list marked non-authoritative against `dishes.csv`; UJ10 Sushi decision left open; 9 taxonomy defects (e.g. a "Vegan" mayonnaise on an egg base) found by a new validator and fixed | this register, `mock-data/check_taxonomy.py` |
| 2026-10-17 | UJ10 option (a): Sushi added as D35 with key ingredients deliberately absent from the catalogue; dish cards keep category icons; owner wants a report-back after each Day-0 step | `mock-data-plan.md` section 4, `mock-data/dishes.csv`, `day-0-walkthrough.md` |
| 2026-10-17 | Owner asked to verify Given/When/Then format. Finding: the Test Plan rows were titles only. Added `verify/test-cases.md` (84 tests in Given/When/Then, IDs unchanged) and one missing "then" in a user-story criterion; PRD acceptance criteria AC-01 to AC-42 remain statements, each mapped to a test | `verify/test-cases.md`, `user-stories.md` |
| 2026-10-17 | Owner approved `verify/test-cases.md` as is (no P0 line-by-line review); PRD acceptance criteria AC-01 to AC-42 stay as statements; GitHub repo `VarunParikh/zest-sous-chef` created, public; commits keep the co-author line | `verify/test-cases.md`, this register |
| 2026-10-17 | Owner amended ADR-003: local-first pluggable vision with Gemini optional; bar 70-80% (precision >= 0.80, recall >= 0.70 gate, recall 0.80 target); latency 10-20 s with a progress bar. Thresholds v2 committed before any run; downstream sync logged as C15 | `ADR-003` v2, `eval/thresholds.yaml`, `open-conflicts.md` C15 |
| 2026-10-17 | Owner confirmed the E3 gate stays recall >= 0.70 and precision >= 0.80, with recall 0.80 as a reported target only (thresholds v2 unchanged). Owner deferred creating a new Gemini key until the local benchmark has run; Gemini is optional, so `.env.example` carries a blank `GEMINI_API_KEY=`. The key pasted in chat is treated as compromised and is not stored in any repository file | `eval/thresholds.yaml` v2, ADR-003 v2 |
| 2026-10-17 | Owner amended ADR-004 to v2: add-ons are dishes suggested for the dish being cooked, from curated pairs plus vector neighbours (weighted RRF, course rule), with an owner target of 100 companion-course dishes and a larger dish total. The Settings Panel wording is logged and resolved as C17 (Panel not edited). ADR-004 v2, ADR index and conflicts pushed as `fe38a4a` | `ADR-004` v2, `open-conflicts.md` C16, C17 |
| 2026-10-17 | Owner asked for the other documents to be updated (doc-sync, C16). Amended and returned to Draft (Rule 2): PRD v0.4, Data Model v0.2, Architecture v0.2, Build Plan v0.2, User Stories v0.3, Test Plan v0.2 with Test Cases, Evaluation Plan v0.2, Mock Data Plan v0.2. Count and wording refreshes only, status unchanged: Product Platforms (dish and pairing rows), Assumptions and Risk Register (A4). ADR-005 not edited (ADR-004 v2: unchanged). No CHANGELOG file exists yet, so this row is the record. **Claude Code stays blocked on these documents under CLAUDE.md until the owner re-approves them** | this register, `open-conflicts.md` C16 |

| 2026-10-17 | Owner re-approved the eight amended documents (PRD v0.4, Data Model v0.2, Architecture v0.2, Build Plan v0.2, User Stories v0.3, Test Plan v0.2 with Test Cases, Evaluation Plan v0.2, Mock Data Plan v0.2); accepted at 127 minimum dishes, the proposed config keys and values (pool 8, ADDON_COURSES side/beverage/dessert), at least 6 companion dishes in the test catalogue, and the proposed add-on evaluation gates (`eval/thresholds.yaml` v3). Also: ADR-004 v1 record and ADR-005 counts refreshed; Data Model aligned to the seed (`pairings.csv` fields `dish_a`/`dish_b`, `soup` course added); expansion of `dishes.csv`, `pairings.csv` and eval datasets approved for Claude Code to build | this register, `eval/thresholds.yaml` |
| 2026-10-17 | Owner resolved C18 with option (c): the add-on price cap applies to the basket cost of the add-on dish, excluding ingredients already in the cart | `open-conflicts.md` C18, `data-model.md` eligibility table |
