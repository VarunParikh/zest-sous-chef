# Claude Code prompts and session plan

Status: working aid for the owner (not a spec). Copy a prompt into the Code tab when its step comes up. Source for blocks and gates: `build-plan.md` sections 5 to 8.

## Tonight's plan (owner available all night)
| Step | Block | Stop and check |
|---|---|---|
| 0 | Kickoff, plan only | You read the plan; you approve |
| 1 | 1.1 scaffold | Health page runs; secret scan prints 0 |
| 2 | 1.2 seed data, tranche 1 (about 20-25 dishes) | You review the validator output and read 5 dishes for culinary sense |
| 3 | 1.2 tranches 2 to 4 | Same review, per tranche |
| 4 | 1.3 engine | T-010 to T-038 pass (real output shown) |
| 5 | 1.4 retrieval and add-ons (stretch) | T-040 to T-049 pass |
| Later | 1.5 model benchmarks (needs multi-GB downloads; do it fresh tomorrow so you can read the numbers) | Gates in `eval/thresholds.yaml` |
Not tonight unless time allows: model downloads, Gemini, anything in Day 2.

## Prompt 0: kickoff (Plan mode)
```
You are building Zest, a web-based AI sous-chef prototype. Read CLAUDE.md first, then follow
docs/epics/zest/build-plan.md sections 5 and 6. Work in plan mode. Start with Day 1 block 1.1.
Rules: no implementation without an approved spec section; tests before code; mock data only;
guardrails in code after retrieval; never write any API key anywhere except the local .env;
use only the dependencies in build-plan section 4 and ask before adding any other; log any
document conflict in docs/core/open-conflicts.md instead of resolving it silently; commit after
each story with a conventional commit and a CHANGELOG line. After each block, run the tests for
that block and report real results (PASS, FAIL, BLOCKED, NOT RUN) before moving on. Stop and ask
me if a Day-1 gate fails. Do not download any language model yet. Leave GEMINI_API_KEY blank in
.env.example (vision is local-first, ADR-003 v2).
```

## Prompt 1: seed data, block 1.2 (after block 1.1 is green)
```
For block 1.2, read docs/core/open-conflicts.md (C16, C17, C18) and ADR-004 v2 first.
Build the companion-course dishes (side, beverage, dessert) in tranches of 20-25, to a target
of 100, at least 127 dishes in total. Every new dish ingredient must resolve to a catalogue
product; extend the lexicon and taxonomy if needed. Extend pairings.csv using
dish_a/dish_b/strength/note. Leave some dishes without a curated pair so the vector list is
exercised. Sushi (D35) stays uncovered by design. Run validators V1-V14 (and check_seed.py,
check_taxonomy.py) after every tranche and commit each tranche separately. Stop after the first
tranche and show me the results. If Day-1 gates slip, ship finished tranches and report the
shortfall. Mock prices and dishes are invented; do not claim culinary accuracy. Do not claim a
result you have not run.
```
Continue with: `Tranche 1 approved. Build tranche 2 under the same rules, then stop.` Repeat per tranche.

## Prompt 2: engine and retrieval, blocks 1.3 and 1.4
```
Proceed to block 1.3, then 1.4, in that order. Write the tests first (T-010 to T-038, then
T-040 to T-049, per verify/test-cases.md), show them failing, then implement. The add-on price
cap follows C18 (basket cost of the add-on dish, excluding ingredients already in the cart).
Stop after each block and report real PASS/FAIL/BLOCKED/NOT RUN with the commands run. If a test
cannot be written because the spec is ambiguous, log it in docs/core/open-conflicts.md and ask me.
```

## Prompt 3: end of session
```
Before we stop: run the full test suite and the seed validators, then report exact commands and
results. Update the approval register decisions log with what was built. Confirm git status is
clean, the secret scan on git history prints 0, and everything is pushed. List what is NOT RUN.
```

## House rules for tonight
- Keep **Manual** mode. A paused session is safe; an unattended session that installs things is not.
- Say **no** to any package not in build-plan section 4, and to any model download before block 1.5.
- If it says "all green" without commands and output, reply: `show me the commands and output`.
- Keep the Mac awake for long runs: in Terminal run `caffeinate -dis` and leave it open.
- Paste any error back to the chat as text.
