from pydantic import BaseModel
from typing import List

class RugAPIResponse(BaseModel):
    status: int
    message: str
    result: dict

class RugAPISearchResponse(BaseModel):
    status: int
    message: str
    result: List[dict]

class RugAPIStringResponse(BaseModel):
    status: int
    message: str
    result: str

def response(result):
    return RugAPIResponse(status=1, message="OK", result=result)

def search(result):
    return RugAPISearchResponse(status=1, message="OK", result=result)

def success(result):
    return RugAPIStringResponse(status=1, message="OK", result=result)

def error(reason: str):
    return RugAPIStringResponse(status=0, message="NOTOK", result=reason)

from pydantic import BaseModel
from typing import List

class AIComment(BaseModel):
    commentType: str
    title: str
    description: str
    code: str

class Holder(BaseModel):
    address: str
    numTokens: float
    percentage: float

class ClusterResponse(BaseModel):
    id: int
    clusters: List[List[Holder]]

class ScoreResponse(BaseModel):
    overallScore: float = None
    supplyScore: float = None
    transferrabilityScore: float = None
    liquidityScore: float = None

class TokenInfo(BaseModel):
    lastUpdated: int = None
    deployer: str = None
    name: str = None
    symbol: str = None
    decimals: int = None
    buyLink: str = None
    twitter: str = None
    telegram: str = None
    webUrl: str = None
    discord: str = None
    marketCap: float = None
    fdv: float = None
    lockedLiquidity: float = None
    burnedLiquidity: float = None
    buyTax: float = None
    sellTax: float = None
    liquidityUsd: float = None
    liquiditySingleSided: float = None
    volume24h: float = None
    circulatingSupply: float = None
    totalSupply: float = None
    totalSupplyPercentage: float = None
    txCount: int = None
    holders: int = None
    latestPrice: float = None

class ChartResponse(BaseModel):
    xMin: float
    xMax: float
    yMin: float
    yMax: float
    numDatapoints: int
    data: List[dict]

class TokenReview(BaseModel):
    tokenInfo: TokenInfo
    score: ScoreResponse
    aiHighlights: List[AIComment]
    top5Holders: List[Holder]
    clusters: ClusterResponse
    chart: ChartResponse

class Chain(BaseModel):
    chainId: str = None
    name: str = None
    logoUrl: str = None
    nativeAsset: str = None

class Token(BaseModel):
    name: str = None
    symbol: str = None
    tokenAddress: str = None
    score: float = None
    deployedAgo: int = None
    refreshedAgo: int = None
    logoUrl: str = None
    chain: Chain = None

class SearchResponse(BaseModel):
    tokens: List[Token]
