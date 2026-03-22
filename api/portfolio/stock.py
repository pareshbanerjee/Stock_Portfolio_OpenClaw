from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

# Thin wrapper to match /api/portfolio/stock -> reuse existing module
try:
    import api.portfolio_stock as _mod
    post_stock = _mod.post_stock
except Exception:
    async def post_stock(request):
        return JSONResponse({'error': 'post_stock handler missing'})

app = Starlette(routes=[Route('/', post_stock, methods=['POST'])])
