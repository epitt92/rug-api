from fastapi import APIRouter
import json, random

from src.v1.shared.dependencies import get_random_score
from src.v1.shared.schemas import Token, ScoreResponse, Score, Chain
from src.v1.search.schemas import SearchResponse
from src.v1.shared.constants import ETHEREUM_CHAIN_ID

tokens = None
with open('src/v1/shared/files/tokens.json') as f:
    tokens = json.load(f).get("tokens")

token_list = list(map(lambda s: s.lower(), tokens.keys()))
token_scores = {}

for token in token_list:
    token_scores[token] = get_random_score(93.2, "High liquidity", 100, "High transferrability")

ETHEREUM = Chain(chainId=ETHEREUM_CHAIN_ID)

router = APIRouter()

@router.get("/", response_model=SearchResponse)
def query_search(query: str = "BTC"):
    """
    Retrieve search results by querying a specific string. The search algorithm will check if the query is contained in the token name, symbol or address.

    __Parameters:__
    - **query** (str): The search string to query.
    """

    _query = query.lower()
    
    results = []
    for token in token_list:
        if _query in token:
            results.append(token)
        elif _query in tokens.get(token).get("name").lower():
            results.append(token)
        elif _query in tokens.get(token).get("symbol").lower():
            results.append(token)

    response = []
    for token in results:
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

    return SearchResponse(items=response)
