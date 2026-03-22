from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

# Thin wrapper to match /api/portfolio/analyze -> reuse existing module
try:
    import api.portfolio_analyze as _mod
    analyze = _mod.analyze
except Exception:
    # fallback noop
    async def analyze(request):
        return JSONResponse({'error': 'analyze handler missing'})

app = Starlette(routes=[Route('/', analyze)])
