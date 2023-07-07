from fastapi import APIRouter
from core.models import ReelResponse
from v1.utils.tokens import reel_response

router = APIRouter()

@router.get("/", response_model=ReelResponse)
def get_token_reel():
    return reel_response
