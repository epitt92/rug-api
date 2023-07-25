from pydantic import BaseModel
from typing import List

from src.v1.shared.schemas import Token

class FeedResponse(BaseModel):
    items : List[Token] = None
