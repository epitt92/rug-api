from pydantic import BaseModel
from typing import List, Optional
from pydantic import HttpUrl
from src.v1.shared.schemas import Token


class MarketDataResponse(BaseModel):
    marketCap: Optional[float] = None
    liquidityUsd: Optional[float] = None
    liquiditySingleSided: Optional[float] = None
    volume24h: Optional[float] = None
    swapLink: HttpUrl = ""
