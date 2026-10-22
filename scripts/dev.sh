#!/usr/bin/env bash
# Start the backend and the frontend dev server together; Ctrl+C stops both.
# Zest 2.0 defaults to 8100 (API) and 5273 (app) so it can run next to Zest 1.0 on 8000 and 5173 (ADR-012).
set -euo pipefail
cd "$(dirname "$0")/.."
API_PORT="${API_PORT:-8100}"
WEB_PORT="${WEB_PORT:-5273}"
[ -d src/frontend/node_modules ] || (cd src/frontend && npm ci --no-audit --no-fund)
.venv/bin/python -m uvicorn backend.api.app:create_app --factory --app-dir src --host 127.0.0.1 --port "$API_PORT" &
API_PID=$!
trap 'kill "$API_PID" 2>/dev/null || true' EXIT INT TERM
echo ""
echo "  Zest 2.0 is starting: open http://localhost:$WEB_PORT  (API on http://127.0.0.1:$API_PORT, health at /health)"
echo ""
ZEST_API="http://127.0.0.1:$API_PORT" WEB_PORT="$WEB_PORT" npm --prefix src/frontend run dev
