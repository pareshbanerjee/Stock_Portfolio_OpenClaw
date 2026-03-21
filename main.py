#!/usr/bin/env python3
# OpenClaw-Style Portfolio Agent (cleaned)
from fastapi import FastAPI
"""
Root shim to keep backwards compatibility after moving backend into `backend/`.

This module re-exports the FastAPI `app` from `backend.main` so existing
commands like `uvicorn main:app` continue to work. Prefer running
`uvicorn backend.main:app` directly.
"""
from backend.main import app  # re-export for compatibility

if __name__ == "__main__":
    print("Run via: uvicorn backend.main:app --reload --port 8001")
    load_dotenv()
