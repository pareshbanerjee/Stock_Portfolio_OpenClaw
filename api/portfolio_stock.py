from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.requests import Request
from ._utils import load_portfolio, save_portfolio


async def post_stock(request: Request):
    stock = await request.json()
    if not stock or not stock.get('ticker'):
        return JSONResponse({'error': "stock with 'ticker' required"}, status_code=400)
    p = load_portfolio()
    stocks = p.get('stocks', [])
    found = False
    for s in stocks:
        if s.get('ticker') == stock.get('ticker'):
            s.update(stock)
            found = True
            break
    if not found:
        stocks.append(stock)
    p['stocks'] = stocks
    ok = save_portfolio(p)
    if not ok:
        return JSONResponse({'error': 'failed to save portfolio'}, status_code=500)
    return JSONResponse({'portfolio': p})


app = Starlette(routes=[Route('/', post_stock, methods=['POST'])])
