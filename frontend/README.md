# OpenClaw Frontend

Dev steps:

Install dependencies:

```bash
cd frontend
npm install
```

Run dev server (Vite):

```bash
npm run dev
```

The Vite server runs on `http://localhost:5173/` and the backend runs on `http://localhost:8000/` (uvicorn). `main.py` has CORS enabled for the Vite dev origin.

Use the "Run Agent" button to call `POST /agent/run` on the backend.
