from fastapi import APIRouter
from core.models import SearchResponse
from v1.utils.tokens import search_response

router = APIRouter()

@router.get("/", response_model=SearchResponse)
def post_search(query: str = "query" ):
    """
    Retrieve search results by query.

    __Parameters:__
    - **query** (str): The search string to query.
    """

    return search_response
