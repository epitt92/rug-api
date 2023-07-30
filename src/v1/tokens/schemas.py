from pydantic import BaseModel, HttpUrl, root_validator, validator, confloat
from typing import List
from enum import Enum

from src.v1.shared.schemas import ScoreResponse, TokenBase
from src.v1.sourcecode.schemas import SourceCodeResponse

######################################################
#                                                    #
#                    AI Schemas                      #
#                                                    #
######################################################

class AIComment(BaseModel):
    commentType: str = None
    title: str = None
    description: str = None
    severity: int = None
    fileName: str = None
    sourceCode: str = None

class AISummary(BaseModel):
    description: str
    numIssues: int
    overallScore: float
    comments: List[AIComment]

######################################################
#                                                    #
#                  Cluster Schemas                   #
#                                                    #
######################################################

class Holder(BaseModel):
    address: str
    numTokens: float
    percentage: float

    @root_validator(pre=True)
    def pre_process(cls, values):
        # Convert tokenAddress to lowercase
        if 'address' in values:
            values['address'] = values['address'].lower()
        return values
    
    @validator('address')
    def validate_address(cls, value):
        if not value.startswith('0x'):
            raise ValueError('Field "address" must be a valid Ethereum address beginning with "0x".')
        if len(value) != 42:
            raise ValueError('Field "address" must be a valid Ethereum address with length 42.')
        return value

class Cluster(BaseModel):
    members: List[Holder]
    percentage: float = None
    numMembers: int = None

    @root_validator(pre=True)
    def pre_process(cls, values):
        values['numMembers'] = len(values['members'])
        values['percentage'] = 0
        for holder in values['members']:
            if isinstance(holder, dict):
                values['percentage'] += holder['percentage']
            elif isinstance(holder, Holder):
                values['percentage'] += holder.percentage
        return values

class ClusterResponse(BaseModel):
    clusters: List[Cluster]
    numClusters: int = None
    totalPercentage: float = None

    @root_validator(pre=True)
    def pre_process(cls, values):
        values['numClusters'] = len(values['clusters'])
        values['totalPercentage'] = 0
        for cluster in values['clusters']:
            if isinstance(cluster, dict):
                values['totalPercentage'] += cluster['percentage']
            elif isinstance(cluster, Cluster):
                values['totalPercentage'] += cluster.percentage
        return values
    
######################################################
#                                                    #
#         Supply & Transferrability Schemas          #
#                                                    #
######################################################

class SeverityEnum(int, Enum):
    neutral = 0
    low = 1
    medium = 2
    high = 3

class ContractItem(BaseModel):
    title: str = None
    description: str = None
    severity: SeverityEnum = None

class ContractResponse(BaseModel):
    items : List[ContractItem]
    numIssues: int = None
    score: confloat(ge=0.0, le=100.0) = None

    @root_validator(pre=True)
    def pre_process(cls, values):
        values['numIssues'] = len(values['items'])
        return values

######################################################
#                                                    #
#         Supply & Transferrability Schemas          #
#                                                    #
######################################################

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

class TokenMetadata(TokenBase, SocialMedia, MarketData):
    contractDeployer: str = None
    lastUpdatedTimestamp: int = None
    txCount: int = None
    holders: int = None
    latestPrice: float = None

######################################################
#                                                    #
#               Info & Review Schemas                #
#                                                    #
######################################################

class TokenInfoResponse(BaseModel):
    tokenSummary: TokenMetadata = None
    score: ScoreResponse = None
    contractSummary: AISummary = None
    holderChart: ClusterResponse = None

class TokenReviewResponse(TokenInfoResponse):
    supplySummary: ContractResponse = None
    transferrabilitySummary: ContractResponse = None
    liquiditySummary: ClusterResponse = None
    sourceCode: SourceCodeResponse = None