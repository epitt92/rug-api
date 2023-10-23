from pydantic import BaseModel
from typing import List

from src.v1.shared.schemas import Token

class TokenInfoResponse(BaseModel):
    marketCap: int = None
    liquidity: int = None
    volume: int = None
    dex_link: str = ''