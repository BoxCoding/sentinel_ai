#!/usr/bin/env bash
# Start Sentinel AI locally: backend on :8000, frontend on :3000.
# Usage: ./scripts/dev.sh          (Ctrl+C stops both)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ ! -x "$ROOT/.venv/bin/uvicorn" ]; then
  echo "Setting up Python venv..."
  python3 -m venv "$ROOT/.venv"
  "$ROOT/.venv/bin/pip" install -q -r "$ROOT/backend/requirements-demo.txt" || \
  "$ROOT/.venv/bin/pip" install -q fastapi "uvicorn[standard]" pydantic pydantic-settings \
    "python-jose[cryptography]" bcrypt python-multipart httpx scikit-learn pandas numpy \
    joblib structlog
fi

if [ ! -f "$ROOT/data/samples/weather_current.csv" ]; then
  "$ROOT/.venv/bin/python" "$ROOT/data/generators/generate.py"
fi

if [ ! -d "$ROOT/frontend/node_modules" ]; then
  echo "Installing frontend deps..."
  (cd "$ROOT/frontend" && npm install)
fi

echo "Starting backend on http://localhost:8000 (docs at /docs)..."
"$ROOT/.venv/bin/uvicorn" --app-dir "$ROOT/backend" app.main:app --port 8000 &
BACK_PID=$!
trap 'kill $BACK_PID 2>/dev/null' EXIT

echo "Starting frontend on http://localhost:3000 ..."
(cd "$ROOT/frontend" && npm run dev -- -p 3000)
