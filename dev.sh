#!/usr/bin/env bash
set -euo pipefail

# dev.sh — single-command developer script
# Usage: ./dev.sh

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

echo "[dev.sh] repo: $REPO_ROOT"

# Ensure .env exists
if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
  echo "[dev.sh] Copied .env.example -> .env (edit .env to add OPENAI_API_KEY)"
fi

# Create venv if missing and install requirements
if [ ! -d .venv ]; then
  echo "[dev.sh] Creating Python venv .venv"
  python3 -m venv .venv
fi

# Activate venv for installing
# shellcheck source=/dev/null
. .venv/bin/activate

echo "[dev.sh] Installing Python requirements (this may take a moment)"
pip install --upgrade pip
pip install -r requirements.txt

mkdir -p logs

# Helper to check port
port_in_use() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
  else
    # fallback (may be less accurate)
    ss -ltn | grep -q ":$1" || true
  fi
}

# Start backend on 8001 (skip if port in use)
BACKEND_PORT=8001
if port_in_use "$BACKEND_PORT"; then
  echo "[dev.sh] Backend port $BACKEND_PORT already in use — skipping start"
else
  echo "[dev.sh] Starting backend (uvicorn) on port $BACKEND_PORT"
  # backend moved into backend/main.py; run via module path
  uvicorn backend.main:app --reload --port "$BACKEND_PORT" > logs/backend.log 2>&1 &
  echo $! > .backend.pid
  echo "[dev.sh] Backend started (logs/backend.log)"
fi

# Start frontend (Vite) on 5173
cd frontend
FRONTEND_PORT=5173
if port_in_use "$FRONTEND_PORT"; then
  echo "[dev.sh] Frontend port $FRONTEND_PORT already in use — skipping start"
else
  echo "[dev.sh] Installing frontend dependencies (silent)"
  npm install --silent
  echo "[dev.sh] Starting Vite dev server"
  npm run dev -- --host > ../logs/frontend.log 2>&1 &
  echo $! > ../.frontend.pid
  echo "[dev.sh] Frontend started (logs/frontend.log)"
fi

echo "\n[dev.sh] Ready. Tail logs with: tail -f logs/backend.log logs/frontend.log"
