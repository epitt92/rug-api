from fastapi import APIRouter, HTTPException
from core.models import ReelResponse, Token
from v1.utils.tokens import ethereum
import requests, random

router = APIRouter()

@router.get("/")
async def get_reel_response():
    try:
        response = requests.get(f'https://api.1inch.io/v5.0/1/tokens')
        response.raise_for_status()
        data = response.json()
        return data.get("tokens")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hot", response_model=ReelResponse)
async def get_hot_tokens(limit: int = 10):
    tokens = await get_reel_response()

    keys = list(tokens.keys())
    output_keys = random.sample(keys, limit)

    return ReelResponse(items=[Token(name=tokens[key]['name'],
                                        symbol=tokens[key]['symbol'],
                                        tokenAddress=tokens[key]['address'],
                                        score=round(random.uniform(0, 100), 2),
                                        deployedAgo=round(random.uniform(0, 100000), 2),
                                        logoUrl=tokens[key]['logoURI'],
                                        chain=ethereum) for key in output_keys])


@router.get("/new", response_model=ReelResponse)
async def get_new_tokens(limit: int = 10):
    tokens = await get_reel_response()

    keys = list(tokens.keys())
    output_keys = random.sample(keys, limit)

    return ReelResponse(items=[Token(name=tokens[key]['name'],
                                        symbol=tokens[key]['symbol'],
                                        tokenAddress=tokens[key]['address'],
                                        score=round(random.uniform(0, 100), 2),
                                        deployedAgo=round(random.uniform(0, 100000), 2),
                                        logoUrl=tokens[key]['logoURI'],
                                        chain=ethereum) for key in output_keys])


@router.get("/featured", response_model=ReelResponse)
async def get_featured_tokens(limit : int = 10):
    tokens = await get_reel_response()

    keys = list(tokens.keys())
    output_keys = random.sample(keys, limit)

    return ReelResponse(items=[Token(name=tokens[key]['name'],
                                        symbol=tokens[key]['symbol'],
                                        tokenAddress=tokens[key]['address'],
                                        score=round(random.uniform(0, 100), 2),
                                        deployedAgo=round(random.uniform(0, 100000), 2),
                                        logoUrl=tokens[key]['logoURI'],
                                        chain=ethereum) for key in output_keys])
