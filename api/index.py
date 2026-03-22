from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route


async def root(request):
    return JSONResponse({'message': 'SmartFolio serverless API root'})


app = Starlette(routes=[Route('/', root)])
