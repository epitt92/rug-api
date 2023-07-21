from pydantic import BaseModel
from typing import List

class AIComment(BaseModel):
    commentType: str = None
    title: str = None
    description: str = None
    code: str = None

class AISummary(BaseModel):
    description: str
    numIssues: int

class Holder(BaseModel):
    address: str
    numTokens: float
    percentage: float

class ClusterResponse(BaseModel):
    top5Holding: float = 0.73
    clusters: List[List[Holder]]

class Score(BaseModel):
    value: float = None
    description: str = None

class ScoreResponse(BaseModel):
    overallScore: float = None
    supplyScore: Score = None
    transferrabilityScore: Score = None
    liquidityScore: Score = None

class ChartData(BaseModel):
    timestamp: int
    price: float
    volume: float
    marketCap: float

class ChartResponse(BaseModel):
    priceMin: float
    priceMax: float
    marketCapMin: float
    marketCapMax: float
    timestampMin: float
    timestampMax: float
    numDatapoints: int
    latestPrice: float = None
    latestReturn: float = None
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
    score: ScoreResponse = None
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

class SourceCode(BaseModel):
    filename: str = None
    sourceCode: str = None

class TokenMetadata(BaseModel):
    name: str = None
    symbol: str = None
    tokenAddress: str = None
    contractDeployer: str = None
    decimals: int = None
    deployedAgo: int = None
    lastUpdatedTimestamp: int = None
    logoUrl: str = None
    chain: Chain = None
    twitter: str = None
    telegram: str = None
    discord: str = None
    webUrl: str = None
    buyLink: str = None
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

class TokenInfoResponse(BaseModel):
    tokenMetadata: TokenMetadata = None
    score: ScoreResponse = None
    aiSummary: AISummary = None
    topHolders: ClusterResponse = None

class TokenReviewResponse(BaseModel):
    contractInfo: ContractResponse = None
    aiComments: List[AIComment] = None
    clusters: ClusterResponse = None

class ReelResponse(BaseModel):
    items : List[Token] = None
