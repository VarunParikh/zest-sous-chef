# Zest AI Sous-Chef: one-command setup and run on macOS (NFR-08).
PYTHON ?= python3.12
VENV := .venv
PY := $(VENV)/bin/python
RESULTS := docs/epics/zest/verify/test-results

.PHONY: setup dev test scan health

setup: ## create the venv and install pinned dependencies; create .env from the example if missing
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install -q --upgrade pip
	$(PY) -m pip install -q -r requirements.lock.txt
	@test -f .env || (cp .env.example .env && echo "Created .env from .env.example")

dev: ## run the backend on 127.0.0.1:8000 (health page at /health)
	$(PY) -m uvicorn backend.api.app:create_app --factory --app-dir src --host 127.0.0.1 --port 8000 --reload

test: ## unit, contract and acceptance tests (fakes only)
	@mkdir -p $(RESULTS)
	$(PY) -m pytest --junitxml=$(RESULTS)/latest.xml -rA

scan: ## secret scan of the working tree and full git history (T-106)
	$(PY) -I scripts/secret_scan.py

health: ## print the health JSON from a running backend
	@curl -s http://127.0.0.1:8000/api/v1/health | $(PY) -m json.tool
