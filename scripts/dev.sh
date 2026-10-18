#!/usr/bin/env bash
# Start the backend (127.0.0.1:8000) and the frontend dev server (http://localhost:5173) together; Ctrl+C stops both.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d src/frontend/node_modules ] || (cd src/frontend && npm ci --no-audit --no-fund)
.venv/bin/python -m uvicorn backend.api.app:create_app --factory --app-dir src --host 127.0.0.1 --port 8000 &
API_PID=$!
trap 'kill "$API_PID" 2>/dev/null || true' EXIT INT TERM
echo ""
echo "  Zest is starting: open http://localhost:5173  (API on http://127.0.0.1:8000, health at /health)"
echo ""
npm --prefix src/frontend run dev
