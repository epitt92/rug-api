from pydantic import BaseModel, HttpUrl
from typing import List
from enum import Enum

from src.v1.shared.schemas import ScoreResponse, Token

class AIComment(BaseModel):
    commentType: str = None
    title: str = None
    description: str = None
    code: str = None

class AISummary(BaseModel):
    description: str
    numIssues: int
    comments: List[AIComment]

class Holder(BaseModel):
    address: str
    numTokens: float
    percentage: float

class ClusterResponse(BaseModel):
    top5Holding: float = 0.73
    clusters: List[List[Holder]]

class ContractItem(BaseModel):
    title: str = None
    section: str = None
    generalDescription: str = None
    description: str = None
    value: float = None
    severity: int = None

class ContractResponse(BaseModel):
    items : List[ContractItem] = None

class SocialMedia(BaseModel):
    twitter: HttpUrl = None
    telegram: HttpUrl = None
    discord: HttpUrl = None
    webUrl: HttpUrl = None
    buyLink: HttpUrl = None

class MarketData(BaseModel):
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

class TokenMetadata(Token, SocialMedia, MarketData):
    contractDeployer: str = None
    lastUpdatedTimestamp: int = None
    txCount: int = None
    holders: int = None

class TokenInfoResponse(BaseModel):
    tokenMetadata: TokenMetadata = None
    score: ScoreResponse = None
    aiSummary: AISummary = None
    topHolders: ClusterResponse = None

class TokenReviewResponse(BaseModel):
    contractInfo: ContractResponse = None
    clusters: ClusterResponse = None
