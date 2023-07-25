from fastapi import APIRouter

from src.v1.chart.endpoints import router as chart_router
from src.v1.search.endpoints import router as search_router
from src.v1.feeds.endpoints import router as feeds_router
from src.v1.tokens.endpoints import router as tokens_router
from src.v1.sourcecode.endpoints import router as sourcecode_router

v1_router = APIRouter(prefix='/v1')

v1_router.include_router(chart_router, prefix="/chart", tags=["Chart Endpoints"])
v1_router.include_router(search_router, prefix="/search", tags=["Search Endpoints"])
v1_router.include_router(feeds_router, prefix="/tokens", tags=["Feed Endpoints"])
v1_router.include_router(tokens_router, prefix="/tokens", tags=["Token Endpoints"])
v1_router.include_router(sourcecode_router, prefix="/sourcecode", tags=["Source Code Endpoints"])
