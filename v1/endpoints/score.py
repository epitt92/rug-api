from fastapi import APIRouter, HTTPException
from core.models import response, error, success
from core.dummy import tokens
import random

router = APIRouter()

score_mapping = {1: {}}

@router.get("/scores/{chain_id}/{token_address}")
def scores(chain_id: int, token_address: str):
    if chain_id not in score_mapping:
        raise HTTPException(status_code=400, detail=f"Chain ID {chain_id} is not supported.")
    
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is not valid.")
    
    _token_address = token_address.lower()

    if _token_address not in score_mapping[chain_id]:
        score_mapping[chain_id][_token_address] = {"token_address": token_address, "overall_score": int(random.randint(0, 100)), "liquidity_score": int(random.randint(0, 100)), "transferability_score": int(random.randint(0, 100)), "supply_score": int(random.randint(0, 100))}
    
    return response(score_mapping[chain_id][_token_address])
