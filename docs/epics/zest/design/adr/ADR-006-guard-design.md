# ADR-006: Design of the input guard: rules first, optional classifier
- **Status:** Proposed (to be measured Day 1)
- **Date:** 2026-10-17
- **Decision owner:** VJP (product owner); drafted by Claude
- **Authorisation:** Owner direction: guardrails must be robust; the guard design itself is not decided.

## Context
Every user message and every fetched text (transcripts, descriptions) must be screened for off-topic, hazardous and prompt-injection content (FR-10, 12), without blocking ordinary cooking language such as "attack the onions". The guard must not depend on the main model behaving well.

## Decision drivers
- Block rate on attacks
- False-positive rate on ordinary cooking talk, including Hinglish
- Latency and memory
- Testability and determinism

## Options considered
| Option | Pros | Cons |
|---|---|---|
| Rules only (patterns, allow-lists, structural checks) | Deterministic, fast, testable | Brittle against paraphrase |
| Rules plus a small local safety classifier (Llama Guard is a candidate) | Catches paraphrase | Extra model in memory; availability to verify |
| Prompt-only guard in the main model | Simple | Constitution forbids relying on prompts alone |

## Decision
**Not yet decided.** The default plan is rules first with the classifier added only if the benchmark shows rules miss attacks the classifier catches at an acceptable memory cost.

## Rationale
Measured block and false-positive rates decide whether the extra model is justified.

## Consequences
- **Positive:** A data-backed guard design.
- **Negative:** Decision deferred; tests written before the final choice must be implementation-agnostic.
- **Neutral:** None identified.

## Risks and mitigations
- Over-blocking cooking language: include benign hard cases in the set
- Indirect injection in transcripts: wrap fetched text as data (FR-12) regardless of guard choice

## Implementation and rollout
- `guard/` module with a single `screen()` interface
- `scripts/benchmark/guard.py`
- Guard tests are build-failing (G4)

## Validation / rollback
Rollback: switch between rules-only and rules plus classifier by config.

## Evidence to be measured on Day 1
| Measure | Method |
|---|---|
| Block rate and false-positive rate | 40 prompts in English and Hinglish: attacks, off-topic, hazardous, and benign cooking phrases |
| Latency and memory | Per prompt; with and without the classifier |
Results go in `verify/benchmarks/guard.md`. Whether Llama Guard (or another model) is available through Ollama is not verified and is checked on Day 1.

## Related documents
PRD FR-10, 12; AC-15, 21, 22; Risk R5; OWASP LLM Top 10.
