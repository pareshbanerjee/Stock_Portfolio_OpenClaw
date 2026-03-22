from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.requests import Request
from ._utils import run_agent


async def run_agent(request: Request):
    payload = await request.json()
    goal = payload.get('goal', 'Optimize portfolio')
    max_steps = int(payload.get('max_steps', 20))
    max_seconds = int(payload.get('max_seconds', 30))
    res = run_agent(goal, max_steps=max_steps, max_seconds=max_seconds)
    return JSONResponse(res)


app = Starlette(routes=[Route('/', run_agent, methods=['POST'])])
