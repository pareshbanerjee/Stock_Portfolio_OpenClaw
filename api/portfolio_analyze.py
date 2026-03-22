from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from ._utils import load_portfolio, analyze_stock_simple


async def analyze(request):
    p = load_portfolio()
    stocks = p.get('stocks', [])
    analyses = []
    for s in stocks:
        ticker = s.get('ticker')
        if not ticker:
            continue
        analyses.append({'ticker': ticker, 'analysis': analyze_stock_simple(ticker)})
    return JSONResponse({'portfolio': p, 'analyses': analyses})


app = Starlette(routes=[Route('/', analyze)])
