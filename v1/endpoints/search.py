from fastapi import APIRouter
from core.models import search
from core.dummy import tokens
import random

router = APIRouter()

@router.post("/search/{query}")
def post_search(query: str):
    """
    Retrieve search results by query.

    __Parameters:__
    - **query** (str): The search string to query.

    __Returns:__
    - **200 OK** (response model): Returns the search result details as a JSON response.
    """
    result = [{'token_address': token, 'chain_id': 1} for token in tokens]
    
    random.shuffle(result)
    
    return search(result)
