from fastapi import APIRouter
import random

router = APIRouter()

@router.get("/")
def ping():
    return {"message": True}

@router.get("/scores")
def scores(contract_address: str):
    scores = {"contractAddress": contract_address, "rugScore": int(random.randint(0, 100)), "liquidityScore": int(random.randint(0, 100)), "transferabilityScore": int(random.randint(0, 100)), "supplyScore": int(random.randint(0, 100))}
    return {"message": scores}
