from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.requests import Request
from ._utils import load_portfolio, save_portfolio


async def delete_stock(request: Request):
    ticker = request.path_params.get('ticker')
    if not ticker:
        return JSONResponse({'error': 'ticker required'}, status_code=400)
    p = load_portfolio()
    stocks = p.get('stocks', [])
    new = [s for s in stocks if s.get('ticker') != ticker]
    p['stocks'] = new
    ok = save_portfolio(p)
    if not ok:
        return JSONResponse({'error': 'failed to save portfolio'}, status_code=500)
    return JSONResponse({'portfolio': p})


app = Starlette(routes=[Route('/', delete_stock, methods=['DELETE'])])
