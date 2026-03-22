from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

# Thin wrapper to match /api/agent/run -> reuse existing module
try:
    import api.agent_run as _mod
    run_agent = _mod.run_agent
except Exception:
    async def run_agent(request):
        return JSONResponse({'error': 'run_agent handler missing'})

app = Starlette(routes=[Route('/', run_agent, methods=['POST'])])
