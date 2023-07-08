from fastapi import APIRouter
from core.models import SearchResponse
from v1.utils.tokens import search_response

router = APIRouter()

@router.post("/", response_model=SearchResponse)
def post_search(query: str ):
    """
    Retrieve search results by query.

    __Parameters:__
    - **query** (str): The search string to query.
    """

    return search_response
