from fastapi import APIRouter, HTTPException
from core.models import response, error, success
import random
from core.models import ScoreResponse
router = APIRouter()

score_mapping = {1: {}}

@router.get("/{chain_id}/{token_address}", response_model=ScoreResponse)
def scores(chain_id: int, token_address: str):
    if chain_id not in score_mapping:
        raise HTTPException(status_code=400, detail=f"Chain ID {chain_id} is not supported.")
    
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is not valid.")
    
    _token_address = token_address.lower()

    if _token_address not in score_mapping[chain_id]:
        score_mapping[chain_id][_token_address] = {"overallScore": int(random.randint(0, 100)), "liquidityScore": int(random.randint(0, 100)), "transferrabilityScore": int(random.randint(0, 100)), "supplyScore": int(random.randint(0, 100))}
    
    return score_mapping[chain_id][_token_address]
