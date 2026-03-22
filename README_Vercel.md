Vercel Deployment Guide

Overview

This repository contains a Vite + React frontend in `frontend/` and a Python FastAPI backend in `backend/`.

You have two choices for running the backend when deploying the frontend to Vercel:

- Recommended: deploy the backend as a separate service (Render, Railway, Cloud Run) and point the frontend to it via the `VITE_API_BASE` environment variable.
- Option B (Serverless on Vercel): port the backend endpoints to Vercel Serverless Functions in `api/`.

This README covers Option B scaffolding notes and a minimal example.

Quick steps (Option B - Serverless Functions)

1. Add your serverless Python function files under `api/` (one file per endpoint). Vercel's Python runtime supports ASGI/Starlette/Flask apps.

2. Install required dependencies and vendor them or use a `requirements.txt` if you plan to use external packages.

3. Set environment variables in the Vercel dashboard (Project → Settings → Environment Variables):
   - `OPENAI_API_KEY` (if you use OpenAI)
   - any other secrets your functions require

4. Deploy the project to Vercel. The provided `vercel.json` routes `/api/*` to files under `api/`.

Important Notes / Limitations

- Vercel Serverless functions have cold starts and execution time limits; they are not suited for long-running background tasks.
- If your backend requires compiled dependencies (e.g., heavy numerical libraries), those may not run in Vercel's environment.
- For complex apps, the recommended path is to host the FastAPI app on Render/Cloud Run and point the frontend to it.

Example Python function template (Starlette)

Create a file `api/portfolio_get.py` with contents similar to:

```
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.requests import Request

app = Starlette()

@app.route('/api/portfolio', methods=['GET'])
async def get_portfolio(request: Request):
    # Minimal example: read the backend JSON file (if you included it) or return a placeholder
    try:
        import os, json
        path = os.path.join(os.getcwd(), 'backend', 'portfolio.json')
        with open(path, 'r') as f:
            data = json.load(f)
        return JSONResponse({'portfolio': data})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)
```

This requires `starlette` to be available. Add a `requirements.txt` with `starlette` and any other dependencies you need, and ensure Vercel installs them.

Proxying to another backend

If you prefer to keep your FastAPI backend running elsewhere, add `VITE_API_BASE` in Vercel to the backend URL and leave the `api/` folder empty; the frontend will use that base URL.

CORS

Make sure any backend you deploy allows CORS from your Vercel domain. For FastAPI, something like:

```
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["https://your-vercel-domain.vercel.app"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
```

Final notes

I can:
- Scaffold example Python functions for each endpoint in `api/` (GET `/`, `/portfolio`, POST `/portfolio/stock`, DELETE `/portfolio/stock/{ticker}`, GET `/portfolio/analyze`, POST `/agent/run`).
- Generate a `requirements.txt` and example `vercel.json` (already added).

Tell me if you want me to scaffold the functions now (I will create simple Starlette-based handlers that read/write `backend/portfolio.json` and proxy heavier logic to the existing `backend/main.py` as needed).