# SmartFolio

SmartFolio — OpenClaw-style portfolio assistant.

![CI](https://github.com/pareshbanerjee/Stock_Portfolio_OpenClaw/actions/workflows/ci.yml/badge.svg)

Overview

- Frontend: `frontend/` (Vite + React)
- Backend: `backend/` (FastAPI)
- Vercel serverless scaffolding: `api/`

See `README_Vercel.md` for deployment instructions.

DEV RUN:
Frontend in Dev:
npm run dev -- --host
Backend in Dev:
uvicorn main:app --reload --port 8001
