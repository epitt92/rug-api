from pydantic import BaseModel, confloat
from typing import List, Dict

from src.v1.shared.schemas import Chain

class Node(BaseModel):
    address: str = None
    numTokens: float = None
    percentTokens: confloat(gt=0.0, lt=1.0) = None


class Transfer(BaseModel):
    fromAddress: str = None
    toAddress: str = None
    txHash: str = None
    token: str = None
    amount: float = None
    timestamp: int = None


class Edge(BaseModel):
    fromNode: Node = None
    toNode: Node = None
    metadata: Transfer = None


class Graph(BaseModel):
    nodes: List[Node] = None
    edges: List[Edge] = None
    degreeMapping: Dict[str, int] = None
    numNodes: int = None
    numEdges: int = None


class ConnectedComponent(BaseModel):
    componentPercentage: float = None

    numMembers: int = None
    numTransfers: int = None
    numNodes: int = None
    numTokens: float = None

    averageHolding: float = None

    fullGraph: Graph = None
    componentGraph: Graph = None

    nodePercentages: Dict[str, float] = None
    nodeTokens: Dict[str, int] = None


class ClusterResponse(BaseModel):
    tokenAddress: str = None
    chain: Chain = None
    timestamp: int = None
    numClusters: int = None
    clusters: List[ConnectedComponent] = None
