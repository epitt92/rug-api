from fastapi import APIRouter

from src.v1.search.schemas import SearchResponse

router = APIRouter()

@router.get("/", response_model=SearchResponse)
def query_search(query: str):
    """
    Retrieve search results by querying a specific string. The search algorithm will check if the query is contained in the token name, symbol or address.

    __Parameters:__
    - **query** (str): The search string to query.
    """

    return SearchResponse(items=[])
