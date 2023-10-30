from pydantic import BaseModel, root_validator, validator
from typing import List, Optional
from pydantic import HttpUrl
from src.v1.shared.schemas import Token

from src.v1.shared.models import ChainEnum, DexEnum

class TokenData(BaseModel):
    chain: ChainEnum
    token_address: str
    dex: DexEnum = DexEnum.uniswapv2

    @root_validator(pre=True)
    def pre_process(cls, values):
        values["token_address"] = values["token_address"].lower()
        return values

    @validator("token_address")
    def validate_token_address(cls, value):
        if not value.startswith("0x"):
            raise ValueError(
                'Field "token_address" must be a valid Ethereum address beginning with "0x".'
            )
        if len(value) != 42:
            raise ValueError(
                'Field "token_address" must be a valid Ethereum address with length 42.'
            )
        return value

class MarketDataResponse(BaseModel):
    tokenData: Optional[TokenData] = None
    marketCap: Optional[float] = None
    liquidityUsd: Optional[float] = None
    liquiditySingleSided: Optional[float] = None
    volume24h: Optional[float] = None
    swapLink: Optional[HttpUrl] = ""
