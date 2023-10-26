from pydantic import BaseModel
from typing import List, Optional
from pydantic import HttpUrl
from src.v1.shared.schemas import Token

from src.v1.shared.models import ChainEnum, DexEnum

class MarketDataResponse(BaseModel):
    marketCap: Optional[float] = None
    liquidityUsd: Optional[float] = None
    liquiditySingleSided: Optional[float] = None
    volume24h: Optional[float] = None
    swapLink: HttpUrl = ""

class TokenData(BaseModel):
    chain: ChainEnum
    token_address: str
    dex: DexEnum = DexEnum.uniswapv2