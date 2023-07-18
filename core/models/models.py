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
    logoUrl: str = None

class ChartData(BaseModel):
    timestamp: int
    price: float
    volume: float
    marketCap: float

class ChartResponse(BaseModel):
    xMin: float
    xMax: float
    yMin: float
    yMax: float
    numDatapoints: int
    data: List[ChartData]

class Chain(BaseModel):
    chainId: int = None
    name: str = None
    logoUrl: str = None
    nativeAsset: str = None

class Token(BaseModel):
    name: str = None
    symbol: str = None
    tokenAddress: str = None
    score: float = None
    deployedAgo: int = None
    logoUrl: str = None
    chain: Chain = None

class SearchResponse(BaseModel):
    items: List[Token]

class ContractItem(BaseModel):
    title: str = None
    section: str = None
    generalDescription: str = None
    description: str = None
    value: float = None
    severity: int = None

class ContractResponse(BaseModel):
    items : List[ContractItem] = None

class TokenReview(BaseModel):
    tokenInfo: TokenInfo = None
    score: ScoreResponse = None
    aiHighlights: List[AIComment] = None
    contractInfo: ContractResponse = None
    clusters: ClusterResponse = None
    chart: ChartResponse = None

class ReelResponse(BaseModel):
    items : List[Token] = None
