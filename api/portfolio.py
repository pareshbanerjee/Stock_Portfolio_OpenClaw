from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.requests import Request
from ._utils import load_portfolio, save_portfolio


async def get_portfolio(request: Request):
    return JSONResponse({'portfolio': load_portfolio()})


async def replace_portfolio(request: Request):
    payload = await request.json()
    if not isinstance(payload, dict) or 'stocks' not in payload:
        return JSONResponse({'error': "payload must include 'stocks'"}, status_code=400)
    ok = save_portfolio(payload)
    if not ok:
        return JSONResponse({'error': 'failed to save portfolio'}, status_code=500)
    return JSONResponse({'portfolio': payload})


app = Starlette(routes=[
    Route('/', get_portfolio, methods=['GET']),
    Route('/', replace_portfolio, methods=['POST']),
])
