# from .ai import router as ai_router
# from .liquidity import router as liquidity_router
from .token import router as token_router
from .search import router as search_router
from .sourcecode import router as sourcecode_router
from .tokenreel import router as tokenreel_router

from fastapi import APIRouter

v1_router = APIRouter(prefix="/v1")

# v1_router.include_router(ai_router, prefix="/ai", tags=["AI Endpoints"])
# v1_router.include_router(liquidity_router, prefix="/liquidity", tags=["Liquidity Endpoints"])
v1_router.include_router(token_router, prefix="/token", tags=["Token Endpoints"])
v1_router.include_router(search_router, prefix="/search", tags=["Search Endpoints"])
v1_router.include_router(sourcecode_router, prefix="/sourcecode", tags=["Source Code Endpoints"])
v1_router.include_router(tokenreel_router, prefix="/tokenreel", tags=["Token Reel Endpoints"])
