# Zest AI Sous-Chef: one-command setup and run on macOS (NFR-08).
PYTHON ?= python3.12
VENV := .venv
PY := $(VENV)/bin/python
RESULTS := docs/epics/zest/verify/test-results

.PHONY: setup dev app test test-embedder test-e2e scan health data index eval-decisions

setup: ## create the venv and install pinned dependencies; create .env from the example if missing
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install -q --upgrade pip
	$(PY) -m pip install -q -r requirements.lock.txt
	@test -f .env || (cp .env.example .env && echo "Created .env from .env.example")
	cd src/frontend && npm ci --no-audit --no-fund

dev: ## run the backend on 127.0.0.1:8000 (health page at /health)
	$(PY) -m uvicorn backend.api.app:create_app --factory --app-dir src --host 127.0.0.1 --port 8000 --reload

app: ## start the backend (127.0.0.1:8000) and the frontend (http://localhost:5173) together; Ctrl+C stops both
	./scripts/dev.sh

test: ## unit, contract and acceptance tests (fakes only)
	@mkdir -p $(RESULTS)
	$(PY) -m pytest -m "not embedder and not e2e" --junitxml=$(RESULTS)/latest.xml -rA

test-e2e: ## E2E-001 demo path in headless Chromium (fake model, real backend, built frontend)
	npm --prefix src/frontend run build
	$(PY) -m pytest -m e2e --junitxml=$(RESULTS)/e2e.xml -rA

test-embedder: ## tests that use the real embedding model (downloads it once into data/models/)
	$(PY) -m pytest -m embedder --junitxml=$(RESULTS)/embedder.xml -rA

scan: ## secret scan of the working tree and full git history (T-106)
	$(PY) -I scripts/secret_scan.py

health: ## print the health JSON from a running backend
	@curl -s http://127.0.0.1:8000/api/v1/health | $(PY) -m json.tool

data: ## generate the mock catalogue (1,000+ and 5,000+ sets) and run validators V1-V14 on both
	$(PY) mock-data/build.py
	$(PY) mock-data/build.py --scale 5
	$(PY) mock-data/validate.py
	$(PY) mock-data/validate.py --scale 5
	$(PY) mock-data/check_seed.py
	$(PY) mock-data/check_taxonomy.py

index: ## build or refresh the Chroma index in data/chroma/ with the default embedder
	$(PY) scripts/index.py

TEXT_MODELS ?= llama3.2:3b,qwen2.5:7b,qwen3:4b-instruct
eval-decisions: ## Day-1 decision evidence E5, E4, E1 on the test split (E3 vision is added in stage 2)
	$(PY) scripts/benchmark/retrieval.py --split test
	$(PY) scripts/benchmark/guard.py --split test
	$(PY) scripts/benchmark/text_models.py --split test --models $(TEXT_MODELS)
