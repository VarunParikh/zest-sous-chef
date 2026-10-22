# ADR-012: Run Zest 2.0 side by side with Zest 1.0
- **Status:** Accepted (owner, 2026-10-22, with the Zest 2.0 plan)
- **Date:** 2026-10-22
- **Decision owner:** VJP (product owner); drafted by Claude
- **Authorisation:** The owner asked for Zest 2.0 "hosted on another port so I can run both for comparing". The owner chose:
  - version v2.0.0;
  - both a Mac app and a source run;
  - a "2.0" badge on the icon;
  - development on the branch `zest-2.0`, merged only when approved.
- **Outcome (2026-10-23):** `zest-2.0` was merged into `main` and released as v2.0.0 (tag on commit `85e7661`). The owner chose to keep the branch, locally and on GitHub, as the record of the 2.0 work.

## Context
Zest 2.0 adds six onboarding features (US-42 to US-47). The owner wants to compare it with the released 1.0 (tag `v0.2.0`, `Zest.app`) on the same Mac at the same time. 1.0 uses these resources:

| Resource | Zest 1.0 |
|---|---|
| App port (DMG) | 8000 (or a free port) |
| Source ports | 8000 and 5173 |
| Data folder | `~/Library/Application Support/Zest` |
| Private Ollama port | 11435 |

1.0 cannot be changed, because its release is published.

## Decision drivers
- Both versions run at once with no port, data or process clash.
- 2.0 is never confused with 1.0 (Dock, browser tab, header).
- No second 7 GB model download.
- A 16 GB Mac cannot comfortably hold two copies of the models.
- 1.0 stays exactly as released.

## Decision
| | Zest 1.0 (unchanged) | Zest 2.0 |
|---|---|---|
| Mac app | `Zest.app`, `io.github.varunparikh.zest-sous-chef` | `Zest 2.0.app`, `io.github.varunparikh.zest-sous-chef.v2` |
| App port (DMG) | 8000 or free | **8100** or free |
| Source ports (`make app`) | 8000 / 5173 (from a `v0.2.0` worktree) | **8100 / 5273** (`API_PORT`, `WEB_PORT`) |
| Data folder | `…/Application Support/Zest` | `…/Application Support/Zest 2.0` |
| Private Ollama | 11435 | **11436** |
| Model files | own folder | 1.0's `ollama-models` folder when it exists, else its own |
| Icon, tab, header | "Zest" | badged icon, "Zest 2.0" |

**Model server.** 2.0 reuses an Ollama on 11434 that serves all three models. Otherwise it starts its own on 11436, using the shared model folder.

It never reuses 1.0's private server on 11435. If 1.0 quits, that server stops, and 2.0's backend keeps the server address it was started with (`create_app()` is not changed).

The two Mac apps' launchers each write their own `launcher.json` in their own data folder. A second double-click opens the right app.

## Options considered
| Option | Why not |
|---|---|
| One app with a 1.0/2.0 switch | Not "another app on another port"; a 1.0 view could not be guaranteed to be identical to the release |
| 2.0 reuses 1.0's private Ollama (11435) | 2.0 breaks when 1.0 quits |
| A local proxy in front of every Ollama | Extra moving part for a prototype |
| A separate model folder for 2.0 | A second 7 GB download |

## Consequences
- **Positive:**
  - Both apps run together.
  - 2.0 is clearly labelled.
  - The models are shared, so there's no second download.
- **Negative:**
  - If neither app finds an Ollama on 11434, each starts its own server, and both can hold models in memory at once.
  - The comparison guide therefore tells 16 GB users to run one Ollama (`brew services start ollama`), so both apps share it.
- **Neutral:**
  - The source defaults move from 8000/5173 to 8100/5273 on 2.0 (conflict C78).
  - `make app API_PORT=… WEB_PORT=…` overrides them.

## Risks and mitigations
- **Two Ollama servers using one model folder:** reading is safe. A download by 2.0 while 1.0 is pulling is unlikely, because 1.0 has already downloaded everything when the folder exists.
- **Edition constants drift between the launcher and `Info.plist`:** a unit test (T-127) checks they match.

## Validation / rollback
- **Validation:** T-127 (unit) and T-128 (manual: both apps open together, quitting one leaves the other running, no second download).
- **Rollback:** 1.0 is untouched; delete `Zest 2.0.app` and its data folder.

## Related documents
- ADR-011 (Mac app); US-41 to US-47; C77, C78; build plan.
