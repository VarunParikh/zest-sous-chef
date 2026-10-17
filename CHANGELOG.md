# Changelog

All notable changes to this project are recorded here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Backend scaffold (FastAPI, Python 3.12), `Settings` config from `.env` with architecture §6 defaults, `.env.example`, `make setup|dev|test|scan|health`, and `GET /api/v1/health` plus a `/health` page that report text model, vision provider, fixtures and index status (block 1.1; API Spec endpoint 1, NFR-02).
- Trace module `backend.trace` writing `logs/trace.jsonl`: only the 12 data-model §11 events, strings cut to 120 characters, bytes, data URIs and base64 payloads removed (US-35; NFR-06; T-109 unit level).
- `scripts/secret_scan.py` (`make scan`): stdlib scan of the working tree and full git history for key-shaped strings, masked output, `findings: N` (T-106, S-01). Fake test values carry the `not-a-real-key` marker, which exempts only the loose `GEMINI_API_KEY=` assignment rule.
- `.gitignore` now covers `logs/`, `data/chroma/`, coverage output and generated test results; checked by T-107 (S-07).

### Docs
- Logged C19 (`config.yaml` and `eval/thresholds.yaml` need a YAML parser that is not on the approved list) and added a block 1.1 note to C15 (vision default and health-page wording follow ADR-003 v2).
