# ADR-006: Design of the input guard: rules first, optional classifier
- **Status:** **Accepted (owner, 2026-10-18):** rules plus the `llama-guard3:1b` classifier, chosen by the Day-1 benchmark E4
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
**Decided 2026-10-18:** rules first, then `llama-guard3:1b` on text the rules pass. E4 showed the rules alone miss attacks the classifier catches (9/13 vs 12/13 blocked) at about 1.7 GB and a 53 ms median per call. Evidence and caveats below.

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

## Evidence and decision (Day 1, 2026-10-18)
Approved by the owner on 2026-10-18 ("Approve the ADR-002, 004, 005 and 006 proposals as written"). Evidence: `eval/results/` and `verify/benchmarks/` (see [adr-proposals.md](../../verify/benchmarks/adr-proposals.md)).

- **Evidence (E4, 20 test prompts):**
  - Rules alone: **FAIL**, 9/13 attacks blocked (0.69 against the 0.90 gate). They missed both transcript injections, one direct injection and one hazard.
  - Rules plus `llama-guard3:1b`: **PASS**, 12/13 blocked (0.92; CI 0.67–0.99, not separable), 0/7 false positives.
  - Cost: 1.7 GB resident; classifier call median 53 ms, p95 133 ms. The first cold call took 6.6 s, so the warm-up script must load it.
- **Design:** rules run first (free, deterministic); the classifier runs only when the rules pass the text. Fetched text still goes through spotlighting and the no-authority design, whatever the guard says.
- **Caveats:**
  1. The rules author saw test items G02 and G04 while checking the file format. This is disclosed in every E4 result; the rules were not tuned on the test split.
  2. One injection (G08) passed both arms.
  3. English only.
  4. The end-to-end critical check (an injection must never change the cart) runs with the E9 harness in block 2.
- **Memory budget with all three models resident:** text 2.6 GB + guard 1.7 GB + (optional) nomic 0.3 GB. The vision model chosen in E3 must fit beside these; E3's "no swap" gate tests that.

## Related documents
PRD FR-10, 12; AC-15, 21, 22; Risk R5; OWASP LLM Top 10.
