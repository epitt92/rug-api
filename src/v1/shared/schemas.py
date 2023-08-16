from pydantic import BaseModel, HttpUrl, confloat, constr, validator, root_validator
from enum import Enum

from src.v1.shared.constants import (ETHEREUM_CHAIN_ID, BSC_CHAIN_ID, ARBITRUM_CHAIN_ID, BASE_CHAIN_ID,
        ETHEREUM_CHAIN_NAME, BSC_CHAIN_NAME, ARBITRUM_CHAIN_NAME, BASE_CHAIN_NAME,
        ETHEREUM_LOGO_URL, BSC_LOGO_URL, ARBITRUM_LOGO_URL, BASE_LOGO_URL,
        ETHEREUM_NATIVE_ASSET, BSC_NATIVE_ASSET, ARBITRUM_NATIVE_ASSET, BASE_NATIVE_ASSET)

class Score(BaseModel):
    value: confloat(ge=0.0, le=100.0) = None
    description: constr(max_length=512) = None

class ScoreResponse(BaseModel):
    overallScore: confloat(ge=0.0, le=100.0) = None
    supplyScore: Score = None
    transferrabilityScore: Score = None
    liquidityScore: Score = None

class ChainIdEnum(Enum):
    ethereum = ETHEREUM_CHAIN_ID
    arbitrum = ARBITRUM_CHAIN_ID
    base = BASE_CHAIN_ID

class Chain(BaseModel):
    chainId: ChainIdEnum
    name: str = None
    logoUrl: HttpUrl = None
    nativeAsset: str = None

    @root_validator(pre=True)
    def set_defaults(cls, values: dict) -> dict:
        chain_id = values.get('chainId')
        if chain_id == ETHEREUM_CHAIN_ID:
            values['name'] = ETHEREUM_CHAIN_NAME
            values['logoUrl'] = ETHEREUM_LOGO_URL
            values['nativeAsset'] = ETHEREUM_NATIVE_ASSET
        elif chain_id == ARBITRUM_CHAIN_ID:
            values['name'] = ARBITRUM_CHAIN_NAME
            values['logoUrl'] = ARBITRUM_LOGO_URL
            values['nativeAsset'] = ARBITRUM_NATIVE_ASSET
        elif chain_id == BASE_CHAIN_ID:
            values['name'] = BASE_CHAIN_NAME
            values['logoUrl'] = BASE_LOGO_URL
            values['nativeAsset'] = BASE_NATIVE_ASSET
        return values

class TokenBase(BaseModel):
    name: str = None
    symbol: str = None
    tokenAddress: constr(max_length=42)
    chain: Chain
    logoUrl: HttpUrl = None

    @root_validator(pre=True)
    def pre_process(cls, values):
        # Convert tokenAddress to lowercase
        if 'tokenAddress' in values:
            values['tokenAddress'] = values['tokenAddress'].lower()
        return values
    
    @validator('tokenAddress')
    def validate_token_address(cls, value):
        if not value.startswith('0x'):
            raise ValueError('Field "tokenAddress" must be a valid Ethereum address beginning with "0x".')
        if len(value) != 42:
            raise ValueError('Field "tokenAddress" must be a valid Ethereum address with length 42.')
        return value

class Token(TokenBase):
    decimals: int = None
    score: ScoreResponse = None
    deployedAgo: int = None
