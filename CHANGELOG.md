# Changelog

All notable changes to this project are recorded here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Backend scaffold (FastAPI, Python 3.12), `Settings` config from `.env` with architecture §6 defaults, `.env.example`, `make setup|dev|test|scan|health`, and `GET /api/v1/health` plus a `/health` page that report text model, vision provider, fixtures and index status (block 1.1; API Spec endpoint 1, NFR-02).
- Trace module `backend.trace` writing `logs/trace.jsonl`: only the 12 data-model §11 events, strings cut to 120 characters, bytes, data URIs and base64 payloads removed (US-35; NFR-06; T-109 unit level).
- `scripts/secret_scan.py` (`make scan`): stdlib scan of the working tree and full git history for key-shaped strings, masked output, `findings: N` (T-106, S-01). Fake test values carry the `not-a-real-key` marker, which exempts only the loose `GEMINI_API_KEY=` assignment rule.
- `.gitignore` now covers `logs/`, `data/chroma/`, coverage output and generated test results; checked by T-107 (S-07).- Catalogue generator `backend.catalogue` (`mock-data/build.py`, `make data`): 1,025 variants and 2,086 SKUs from the 342-row taxonomy with seed 20261017 (committed in `mock-data/generated/`), plus a git-ignored 5,125-variant scale set. Tags are derived from the lexicon; brands are invented `MockMart` names; prices, nutrition and stock are mock values (block 1.2, US-36).
- Validators V1 to V14 (`mock-data/validate.py`): run on both sets. V9 (needs the eligibility engine, block 1.3) and V12 (no retrieval query set yet) report NOT RUN; V7 checks stock counts, and its scenario-reference part waits for `stock_scenarios.json`.
- `LeverSet` and `LEVER_OPTIONS` (`backend/session/levers.py`) with the Settings Panel option strings and ranges, used by V14.

### Changed
- Variant ingredient lists carry the product form as the first qualifier when the base product name differs from its lexicon term (`milk (milk powder, skimmed)`), so different products never share an ingredient list (Data Model §1.4). Two taxonomy rows that were still duplicates got a qualifier (`=boneless` on B317 tikka, `=filter mix` on B328 chicory coffee).
- Lexicon: `sarson` is now an alias of `mustard greens` only (it was also on `mustard seeds`; V10 caught the collision); added `non-food item` for household products.
- `dishes.csv` gains `aliases`, `flavour` and `description` columns, back-filled for D01 to D35 (C20); ingredient lines accept a fourth field `opt` for non-essential garnish lines. `check_seed.py` reads the new format.

### Docs
- Logged C19 (`config.yaml` and `eval/thresholds.yaml` need a YAML parser that is not on the approved list) and added a block 1.1 note to C15 (vision default and health-page wording follow ADR-003 v2).
