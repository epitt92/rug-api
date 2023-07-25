from fastapi import APIRouter
import random, json

from src.v1.feeds.schemas import FeedResponse
from src.v1.shared.schemas import Token, ScoreResponse, Score, Chain
from src.v1.shared.constants import ETHEREUM_CHAIN_ID

tokens = None
with open('src/v1/shared/files/tokens.json') as f:
    tokens = json.load(f).get("tokens")

token_list = list(map(lambda s: s.lower(), tokens.keys()))
token_scores = {}

for token in token_list:
    dummyScore = ScoreResponse(
                overallScore=float(random.uniform(0, 100)), 
                liquidityScore=Score(value=float(random.uniform(0, 100)), description="No liquidity description available."), 
                transferrabilityScore=Score(value=float(random.uniform(0, 100)), description="No transferrability description available."), 
                supplyScore=Score(value=float(random.uniform(0, 100)), description="No supply description available.")
            )
    
    token_scores[token] = dummyScore

ETHEREUM = Chain(chainId=ETHEREUM_CHAIN_ID)

router = APIRouter()

async def get_response(limit: int = 10):
    output_tokens = random.sample(token_list, limit)

    response = []

    for token in output_tokens:
        dictionaryItem = tokens.get(token)
        dictionaryResult = {
            "name": dictionaryItem.get("name"),
            "symbol": dictionaryItem.get("symbol"),
            "tokenAddress": token,
            "decimals": dictionaryItem.get("decimals"),
            "logoUrl": dictionaryItem.get("logoUrl"),
            "score": token_scores.get(token),
            "chain": ETHEREUM
        }

        response.append(Token(**dictionaryResult))

    return FeedResponse(items=response)

@router.get("/hot", response_model=FeedResponse)
async def get_hot_tokens(limit: int = 10):
    return await get_response(limit)


@router.get("/new", response_model=FeedResponse)
async def get_new_tokens(limit: int = 10):
    return await get_response(limit)


@router.get("/featured", response_model=FeedResponse)
async def get_featured_tokens(limit : int = 10):
    return await get_response(limit)
