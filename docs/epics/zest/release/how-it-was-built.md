# How Zest was built and planned with Claude

This document answers two questions a reviewer is likely to ask: what has been done so far and how it was done with Claude, and how the project was planned. Every statement is traceable to a file in this repository; file paths are given in backticks. For how the system works, see `docs/epics/zest/design/retrieval-explained.md` and the README.

**Contents**
1. What has been done so far, and how it was done with Claude
2. How the project was planned with Claude

---

## 1. What has been done so far, and how it was done with Claude

### What exists today
Zest is a working prototype with its evidence, published as release `v0.1.0`.

- **Backend (FastAPI):** sessions, an input guard, intent routing, four entry flows (mood, text recipe, YouTube, photo), hybrid retrieval, a guardrail and scoring engine, and a pure-code cart with checkout.
- **Frontend (React):** a split screen, a lever panel, a chat with cards, a "Why this?" panel, an inspector, and a mobile-shaped cart window.
- **Mock data:** a seeded generator produces 1,027 product variants, 2,090 SKUs and 130 dishes. Seventeen validators check the data on every build.
- **Tests:** over 600 automated tests, one browser test of the demo path and one test with the real embedder.
- **Evaluations:** 14 evaluations on the real local models, summarised in a generated evidence report (`docs/epics/zest/verify/report/report.md`).
- **Documents:** PRD, user stories, architecture, 10 decision records (ADRs), API spec, test plan, evaluation plan, security note, README, demo script and a limitations note.

### Where it stands
- Ten evaluations pass. Among them: zero persona violations in about 48,000 checks, zero price mismatches in 200 random carts, and 26 of 26 injected faults handled with a defined fallback.
- Four evaluations fail their gate and were accepted by the owner as known limitations: the input guard, intent accuracy, soft-lever sensitivity and local photo accuracy.
- The overall status is **FAIL** under the project's own pre-registered rule, and the report says so plainly.

### How it was done with Claude
The work ran over three days, in blocks, in Claude Code. Each block followed the same loop:

1. **Plan mode first.** Claude read the documents and wrote a plan, including the exact text of any document amendment. The owner's approval of the plan was the approval of that text.
2. **Tests before code.** Tests were written and shown failing, then the code was written.
3. **One commit per story,** each with a CHANGELOG line, and the test suite run on the exact tree being committed.
4. **Every conflict between documents was logged** (74 conflicts, C1 to C74 in `docs/core/open-conflicts.md`) and resolved by the owner, never silently.
5. **Evidence was pre-registered.** Datasets and thresholds were committed and hashed before any model ran. Anything changed afterwards was rerun and labelled "post-hoc", and the first result was kept.
6. **Nothing was claimed that was not run.** A missing result shows as NOT RUN.

### Where Claude got things wrong, and how it was caught
These are recorded because they show the process catching its own errors:

- `make data` failed silently for a time, because two older seed-check scripts did not understand a new seed marker. It was found when a clean-clone check was run, then fixed with a regression test, and the records were corrected.
- Five benchmark scripts dropped the "post-hoc" flag. It was found while building the evidence report.
- A draft memory figure for a model was wrong ("halved" instead of about a third less). It was caught by checking the draft against the decision record.

### The owner's role
The owner set the brief, approved every plan and every document change, made every judgment call (for example, accepting a failing evaluation as a known limitation), and approved each push to GitHub.

---

## 2. How the project was planned with Claude

### Documents before code
The working rule (in `CLAUDE.md`) was "document first, then code". Nothing was built without an approved spec section. The planning chain, in order:

| Step | Document | Purpose |
|---|---|---|
| 1 | Product vision (the owner's brief) | The source of truth: what to build |
| 2 | Constitution | Non-negotiables: mock data only, guardrails in code, no real payments |
| 3 | Product strategy, research, personas, risk register | Why, for whom, and what could go wrong |
| 4 | Business requirements, PRD, user stories | What exactly, with acceptance criteria |
| 5 | Architecture, data model, API spec, agent design, 10 ADRs | How |
| 6 | Test plan and evaluation plan | How we will know it works, set before any result existed |
| 7 | Build plan | Day-by-day blocks, gates and a cut order |

### Precedence
When documents disagreed, the higher one won: vision, then constitution, then the lever spec, then the design files, then the user journeys. Every conflict was logged.

### A build plan with gates
- **Day 0:** owner setup.
- **Day 1:** data, engine, retrieval and the model decisions. The gate was a benchmark: a local model had to pass.
- **Day 2:** flows, API, UI and evaluations.
- **Day 3:** proving it, then release.

### Honest sizing and a cut order
The plan stated that 40 stories in three days was aggressive. It listed what to cut first: servings scaling, add-on learning, chat cart edits, live stock-outs. Several of those were in fact cut, and each is recorded.

### Decisions by evidence
Choices that were unknown at the start (which text model, which embedder, whether hybrid search beats keyword search) were left open on purpose and decided by benchmarks. The ADRs show the numbers and the owner's decision.

### Approval register
Every document has a version and an approval record (`docs/core/approval-register.md`). Editing an approved document in a way that changes a requirement sends it back to "draft" until the owner re-approves it.

Key files: `docs/epics/zest/build-plan.md`, `docs/epics/zest/claude-code-prompts.md`, `docs/epics/zest/day-0-walkthrough.md`, `docs/core/constitution.md`, `CLAUDE.md`.
