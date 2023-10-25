from pydantic import BaseModel, HttpUrl, root_validator, validator, confloat
from typing import List, Optional
from enum import Enum
import logging

from src.v1.shared.schemas import ScoreResponse, TokenBase
from src.v1.sourcecode.schemas import SourceCodeResponse

######################################################
#                                                    #
#                    AI Schemas                      #
#                                                    #
######################################################

severity_mapping = {"high": 3, "medium": 2, "low": 1}


class AIComment(BaseModel):
    commentType: str = None
    title: str = None
    description: str = None
    severity: int = None
    fileName: str = None
    lines: List[int] = None
    sourceCode: List[str] = None

    @root_validator(pre=True)
    def pre_process(cls, values):
        if values["severity"] in severity_mapping:
            values["severity"] = severity_mapping.get(values["severity"])
        return values


class AISummary(BaseModel):
    numIssues: int
    overallScore: float
    description: str
    comments: List[AIComment]


######################################################
#                                                    #
#                  Cluster Schemas                   #
#                                                    #
######################################################


class Holder(BaseModel):
    address: str
    percentage: float

    @root_validator(pre=True)
    def pre_process(cls, values):
        # Convert tokenAddress to lowercase
        if "address" in values:
            values["address"] = values["address"].lower()
        return values

    @validator("address")
    def validate_address(cls, value):
        if not value.startswith("0x"):
            raise ValueError(
                'Field "address" must be a valid Ethereum address beginning with "0x".'
            )
        if len(value) != 42:
            raise ValueError(
                'Field "address" must be a valid Ethereum address with length 42.'
            )
        return value


class Cluster(BaseModel):
    members: List[Holder]
    percentage: float = None
    numMembers: int = None
    label: Optional[str] = None

    @root_validator(pre=True)
    def pre_process(cls, values):
        values["numMembers"] = len(values["members"])
        values["percentage"] = 0
        for holder in values["members"]:
            if isinstance(holder, dict):
                values["percentage"] += holder["percentage"]
            elif isinstance(holder, Holder):
                values["percentage"] += holder.percentage

        if not values.get("label"):
            values["label"] = "holder"

        return values


class ClusterResponse(BaseModel):
    clusters: List[Cluster]
    numClusters: int = None
    totalPercentage: float = None

    @root_validator(pre=True)
    def pre_process(cls, values):
        values["numClusters"] = len(values["clusters"])
        values["totalPercentage"] = 0
        for cluster in values["clusters"]:
            if isinstance(cluster, dict):
                values["totalPercentage"] += cluster["percentage"]
            elif isinstance(cluster, Cluster):
                values["totalPercentage"] += cluster.percentage
        return values


######################################################
#                                                    #
#         Supply & Transferrability Schemas          #
#                                                    #
######################################################


class ContractItem(BaseModel):
    title: str = None
    description: str = None
    severity: int = None


class ContractResponse(BaseModel):
    items: List[ContractItem]
    numIssues: int = None
    score: confloat(ge=0.0, le=100.0) = None
    description: str = None
    summaryDescription: str = None

    @root_validator(pre=True)
    def pre_process(cls, values):
        values["numIssues"] = len(values["items"])
        return values


######################################################
#                                                    #
#         Supply & Transferrability Schemas          #
#                                                    #
######################################################


class SocialMedia(BaseModel):
    twitter: Optional[HttpUrl] = None
    telegram: Optional[HttpUrl] = None
    discord: Optional[HttpUrl] = None
    webUrl: Optional[HttpUrl] = None
    buyLink: Optional[HttpUrl] = None


class MarketData(BaseModel):
    lockedLiquidity: Optional[float] = None
    burnedLiquidity: Optional[float] = None
    buyTax: Optional[float] = None
    sellTax: Optional[float] = None
    liquidityUsd: Optional[float] = None
    liquiditySingleSided: Optional[float] = None
    volume24h: Optional[float] = None
    circulatingSupply: Optional[float] = None
    totalSupply: Optional[float] = None
    totalSupplyPercentage: Optional[float] = None


class TokenMetadata(TokenBase, SocialMedia, MarketData):
    contractDeployer: Optional[str] = None
    lastUpdatedTimestamp: Optional[int] = None
    txCount: Optional[int] = None
    holders: Optional[int] = None
    latestPrice: Optional[float] = None


class SimulationResponse(BaseModel):
    supplySummary: ContractResponse = None
    transferrabilitySummary: ContractResponse = None
