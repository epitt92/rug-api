from .ai import router as ai_router
from .liquidity import router as liquidity_router
from .token import router as token_router
from .contract import router as contract_router
from .search import router as search_router
from .sourcecode import router as sourcecode_router
from .score import router as score_router

from core.models import response, error, success
from fastapi import APIRouter
import requests, os

v1_router = APIRouter(prefix="/v1")

# v1_router.include_router(ai_router, prefix="/ai", tags=["AI Endpoints"])
# v1_router.include_router(liquidity_router, prefix="/liquidity", tags=["Liquidity Endpoints"])
v1_router.include_router(token_router, prefix="/token", tags=["Token Endpoints"])
v1_router.include_router(contract_router, prefix="/contract", tags=["Contract Endpoints"])
v1_router.include_router(search_router, prefix="/search", tags=["Search Endpoints"])
v1_router.include_router(sourcecode_router, prefix="/sourcecode", tags=["Source Code Endpoints"])
v1_router.include_router(score_router, prefix="/score", tags=["Score Endpoints"])
