from pydantic import BaseModel
from typing import List

from src.v1.shared.schemas import Token

class SearchResponse(BaseModel):
    items: List[Token]
