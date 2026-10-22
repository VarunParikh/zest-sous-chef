# ADR-011: Ship Zest as a self-contained macOS app in a DMG
- **Status:** Accepted in part. Owner decisions D1 to D3 were taken on 2026-10-22; the rest of this text awaits owner review.
- **Date:** 2026-10-22
- **Decision owner:** VJP (product owner); drafted by Claude
- **Authorisation:** On 2026-10-22 the owner asked for a transferable application file that runs on a MacBook with none of the setup installed. The owner chose: models downloaded on first launch (D1); a portable Python and the Ollama macOS release as build-time downloads (D2); an unsigned app (D3).

## Context
Today the README path needs ten things on the reviewer's Mac:
1. Apple's command-line tools
2. Homebrew
3. Python 3.12
4. About 100 pinned Python packages
5. Node 22 and the npm packages
6. Ollama, with the server started by hand
7. Three Ollama models (about 6.9 GB)
8. Chroma's ONNX embedder (about 80 MB)
9. A built Chroma index
10. A `.env` file

Then there are five commands to run. The owner wants a single file that a recipient double-clicks.

## Decision drivers
- No terminal, Homebrew, Python or Node on the recipient's Mac
- Nothing in the app may weaken a guardrail or change recommendation behaviour (Constitution; CLAUDE.md non-negotiables)
- No new runtime Python dependency
- Small enough to share: GitHub Releases cap one file at 2 GB
- An app bundle is read-only (and may be translocated by Gatekeeper), so every runtime write goes elsewhere

## Options considered
| Option | Pros | Cons |
|---|---|---|
| A Python script (`install.py`) | Small | Needs Python 3.12 first, which a clean Mac lacks (`/usr/bin/python3` is a stub that prompts for the command-line tools); needs Homebrew and a terminal |
| A shell installer (`.pkg` or `curl \| sh`) running Homebrew | Uses the README path | Needs an admin password, a terminal or a `.pkg` signing identity; slow; changes the recipient's system |
| **A DMG holding a self-contained `Zest.app`** | Double-click; nothing installed system-wide; one folder to delete | About 1 GB; unsigned without a Developer ID (D3) |
| The same app wrapped in a native window (pywebview) | Feels native | A new dependency; the browser already works |

## Decision
Build a DMG holding `Zest.app` with `make dmg` (`macapp/build_dmg.sh`). The app contains:

- **Python:** a portable CPython 3.12.15 (python-build-standalone `20261003`, SHA-256 checked) with the runtime packages from `requirements.lock.txt` preinstalled and pre-compiled. Test-only packages (pytest, Playwright, coverage and their own dependencies) are left out.
- **Model server:** the Ollama 0.40.5 macOS command-line release (SHA-256 checked), the version the evaluations ran on.
- **The Zest code as it is:**
  - `src/backend` and the pre-built frontend (`src/frontend/dist`)
  - `mock-data` without the 5,000-SKU evaluation set
  - the sample photos
  - `.env.example` copied as the bundle's `.env`, never the developer's `.env`
- **Embedder and index:** Chroma's all-MiniLM-L6-v2 embedder, and a Chroma index built at package time by the bundled Python.

**The launcher** is `macapp/launcher.py`, started by `Contents/MacOS/Zest`. It does five things:
1. **Checks the Mac:** Apple silicon, macOS 14 or newer and free disk space. A plain dialog explains any failure.
2. **Copies runtime data out of the bundle:** the index goes to `~/Library/Application Support/Zest/` on first launch, or when the app version changes. Logs and models also live there.
3. **Picks a model server.** If an Ollama server already runs on `127.0.0.1:11434` with all three models, Zest uses it. Otherwise it starts the bundled Ollama on a private port (`127.0.0.1:11435`) with its own model folder, so it never touches the recipient's own Ollama.
4. **Starts the server:** one uvicorn server on `127.0.0.1` (port 8000, or a free port if 8000 is taken). It serves Zest's unchanged API (`create_app()`), the built frontend, and a "Getting Zest ready" page at `/launcher/`.
5. **Fetches models on first launch (D1):** it pulls any missing model through Ollama's `/api/pull` and shows progress on that page, which opens Zest once every model is present.

The launcher adds routes around the app object. It does not change `src/backend`.

**The Dock app** (`macapp/ZestApp.swift`) is the app's executable, a native app with a Dock icon and no window. It starts the launcher through `zest-server.sh`:
- Clicking the Dock icon, or **Open Zest in Browser** in its menu, reopens Zest in the browser.
- **Quit** (⌘Q, the Dock menu, logout or shutdown) sends SIGTERM, and the launcher stops the API server and any Ollama it started.
- If the server exits by itself, the Dock app quits too. If the Dock app is force-quit, the launcher notices it is orphaned and stops.
- It is compiled with `swiftc -target arm64-apple-macos14.0` at build time, so it runs on macOS 14 or newer whatever the build Mac runs. The compiler comes with Apple's command-line tools, which building already needs; the recipient needs nothing.

*Revised 2026-10-22 after the owner's first test:* an AppleScript dialog first served as the control window. It stayed on top of the browser and reappeared after **Open Zest**, so the Dock app replaced it. An `osacompile` applet was rejected: its stub carries the build Mac's macOS version (27.0) as its minimum, so it would not start on older macOS.

## Rationale
- Python and Ollama ship inside the app, so a clean Mac needs nothing else.
- Serving the built frontend from the API server removes Node from the runtime and keeps one port.
- Downloading the models on first launch keeps the DMG under the 2 GB release limit (D1). The progress page replaces the terminal steps.

## Consequences
- **Positive:** Double-click to run. Nothing is installed system-wide. Removing Zest means deleting `Zest.app` and `~/Library/Application Support/Zest`.
- **Negative:**
  - The app is unsigned (D3). On first open, macOS blocks it, and the recipient must click **System Settings → Privacy & Security → Open Anyway** once.
  - The first launch needs internet and about 7 GB of downloads.
  - The DMG is about 1 GB.
- **Neutral:**
  - The packaged app uses one port instead of two (`make app` keeps two for development).
  - The YouTube saved-copy fallback and the sample photos work offline after setup, as in the README path.

## Risks and mitigations
- **Gatekeeper blocks an unsigned app.** The DMG carries a "Read me first" note with the exact clicks. Signing and notarizing is the documented follow-up if the owner gets a Developer ID.
- **Nested unsigned code** (Python extension modules, Ollama libraries). The whole bundle is ad-hoc signed at build time, as Apple silicon requires.
- **Ports in use.** The launcher picks a free port for the API, and a private Ollama port.
- **The first download fails or stalls midway.** Ollama resumes partial pulls.
  - **Stall watchdog:** a pull with no progress message for 120 s is dropped and retried, up to 3 attempts per model, with "Connection dropped, retrying" on the page.
  - **Then the user decides:** the page shows a plain sentence (the raw error goes to `launcher.log`) and **Try again**. At 100% the page says Verifying or Finishing, never "Downloading 100%".
  - **Optional photo model:** if only the photo model is missing, **Open Zest without photo analysis** opens Zest. Photos then fall back to the labelled sample photos, as for any vision failure (FR-55).
  - *Added 2026-10-22 after the owner's test:* a pull stalled after its large files, the page sat on "Downloading 100%" for about 10 minutes, and there was no way into Zest.
- **Less than 16 GB of RAM.** A warning, not a block, matching the README.
- **The bundle drifts from the repository.** The bundle is built from the working tree by script. `make dmg` refuses to run with uncommitted changes and stamps the commit into the app.

## Implementation and rollout
- `macapp/icon/zest-icon-source.webp`: the owner-supplied icon artwork (2026-10-22). `make_icon.py` cuts its white corners, places it on Apple's 824-in-1024 icon grid and builds `AppIcon.icns`, which is used for the app and as the DMG volume icon.
- `macapp/`: `build_dmg.sh`, `ZestApp.swift` (the Dock app), `zest-server.sh` (starts the launcher), `launcher.py`, `Info.plist`, `runtime-exclude.txt` and `README-first.txt`. The `make dmg` target writes to the git-ignored `macapp/out/`.
- Story US-41, tests T-111 to T-114 (launcher unit tests) and T-115 (a manual check of the clean-Mac launch).

## Validation / rollback
- **Validation:**
  - `make test` covers the launcher's pure logic.
  - The build's smoke step starts the bundled app headless against a fake model server and checks `/health` and `/`.
  - T-115 is a manual launch on a second Mac (NOT RUN until done).
- **Rollback:** delete `macapp/` and the `dmg` target. The README path is unchanged.

## Related documents
- ADR-001 (Python 3.12), ADR-002, ADR-003 and ADR-006 (the three models), ADR-005 (embedder), ADR-010 (frontend build)
- Build plan §4; NFR-08; US-36, US-41; C75, C76
