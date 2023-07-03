from fastapi import APIRouter
from core.models import search
import random
import json

result = None
with open('v1/utils/search.json') as f:
    result = json.load(f)

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
    random.shuffle(result)
    
    return search(result)
