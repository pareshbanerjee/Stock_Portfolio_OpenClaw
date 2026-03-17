#!/usr/bin/env bash
set -euo pipefail

# stop.sh — stop backend and frontend started by dev.sh
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

echo "[stop.sh] repo: $REPO_ROOT"

kill_pid_file() {
  local pidfile="$1"
  if [ -f "$pidfile" ]; then
    pid=$(cat "$pidfile" 2>/dev/null || true)
    if [ -n "$pid" ] && ps -p "$pid" >/dev/null 2>&1; then
      echo "[stop.sh] Killing PID $pid (from $pidfile)"
      kill "$pid" || kill -9 "$pid" || true
      sleep 1
    else
      echo "[stop.sh] No running pid in $pidfile"
    fi
    rm -f "$pidfile"
  else
    echo "[stop.sh] PID file $pidfile not found"
  fi
}

kill_pid_file .backend.pid
kill_pid_file .frontend.pid

# Fallback: try to kill uvicorn or vite processes started in this repo
if pgrep -f "uvicorn main:app" >/dev/null 2>&1; then
  echo "[stop.sh] Killing any remaining 'uvicorn main:app' processes"
  pkill -f "uvicorn main:app" || true
fi

if pgrep -f "vite" >/dev/null 2>&1; then
  echo "[stop.sh] Killing any remaining 'vite' processes"
  pkill -f "vite" || true
fi

echo "[stop.sh] Done"
