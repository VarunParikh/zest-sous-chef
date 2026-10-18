# Release checklist: v0.1.0

Block 3.5 (build plan §5): close the security release blockers (Security Note §7), scan the full history for secrets, then tag `v0.1.0` and push. Checked on 2026-10-19. Statuses: PASS, FAIL, OWNER (the owner must confirm), TO DO.

## Security release blockers (Security Note §7)
| # | Blocker | Evidence | Status |
|---|---|---|---|
| 1a | No secrets in the working tree or the full git history (S-01) | `make scan`: `findings: 0` on tree and history; T-106 | PASS |
| 1b | The Gemini key that was pasted in chat on Day 0 has been rotated (S-01) | Cannot be checked from the repository: the key lives only in the owner's git-ignored `.env`, and it is never printed | PASS: owner confirmed on 2026-10-19 that the Day-0 key is revoked |
| 2 | Photo notice, EXIF stripping and no-persistence tests pass (S-03) | T-102 (GPS removed); T-103 (no image written to disk); T-109 (no image in the trace); the consent test (`test_gemini_opt_in_asks_consent_before_any_upload_leaves`). The 11 committed sample photos carry no GPS, device or date EXIF data | PASS |
| 3 | Injection tests pass for chat, transcript and image text (S-02) | Chat: T-070 to T-072, guard rule tests. Transcript: MSG-INJECT-DATA tests in the YouTube flow; E9 injection check, 0 cart changes in 36 attacks. Image text: `test_s02_text_read_from_a_photo_is_data_not_instructions` (added 2026-10-19; it covers existing behaviour and passed on its first run) | PASS |
| 4 | Upload validation and URL-handling tests pass (S-04, S-05) | T-089 (wrong type, oversize, spoofed, two images); T-104 (`file://`, internal IPs, look-alike domains, no fetch) | PASS |
| 5 | A rendering test shows markup is inert (S-06) | T-075 (E2E, added 2026-10-19): markup and script strings in messages display as text and execute nothing. It covers existing behaviour and passed on its first run | PASS |
| 6 | `.gitignore` covers `.env`, `logs/`, `data/chroma/` and uploads (S-07); repository review done (S-11) | T-107. Review on 2026-10-19:<br>• Tracked secret-like files: only `.env.example` and the scanner's own files.<br>• Nothing is tracked under `logs/` or `data/`.<br>• Brands are generic ("MockMart …").<br>• Transcripts are own-written narrations.<br>• Sample photos are the owner's own, with EXIF clean.<br>• The two large files are the owner's mockups, approved for publishing (2026-10-17) | PASS |
| 7 | Dependencies pinned, each approved by the owner (S-10) | Compared by hand on 2026-10-19: every direct dependency matches the build plan §4 list (plus PyYAML, approved in C19).<br>• Python, 14 in `requirements.txt`: fastapi, uvicorn, pydantic, python-dotenv, httpx, chromadb, rank-bm25, Pillow, youtube-transcript-api, python-multipart, PyYAML, pytest, pytest-playwright, coverage.<br>• Frontend, 7 in `package.json`: react, react-dom, vite, tailwindcss, typescript, @types/react, @types/react-dom.<br>Transitive versions are pinned in `requirements.lock.txt` and `package-lock.json`. `tests/unit/test_dependencies.py` checks only the two block 2.4 pins | PASS |

## Reviewer can run it from the README
Checked on 2026-10-19 from fresh clones of the committed repository, on the demo Mac:
- `make setup`
- `make index`: one transient embedder download failure; the retry succeeded
- `make test`, `make test-e2e`, `make test-embedder`, `make data`
- `make app`, then the health endpoint and a real chat through the frontend: all succeed
- The README screenshot was taken from that run

The README lists the prerequisites a fresh Mac needs: command-line tools, Python 3.12, Node 22 or newer, a running Ollama server, free ports, and the Playwright browser for the E2E tests. **Not checked:** a different Mac model, Intel, or Linux.

## Still to do
| Item | Owner | Status |
|---|---|---|
| Block 3.4: two rehearsals on the demo laptop (Test Plan §9), the network-off test and a backup screen recording, with the results written into `prototyping-feedback.md` §5 | Owner | **TO DO** (deferred by the owner on 2026-10-19; the release can go ahead without it) |
| Confirm the Day-0 Gemini key is revoked (1b) | Owner | Done (2026-10-19) |
| Tag `v0.1.0` and push to the public repository | Owner approval | Done (owner approved 2026-10-19) |
