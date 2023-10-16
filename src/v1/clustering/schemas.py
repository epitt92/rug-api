from pydantic import BaseModel, confloat, root_validator, validator
from typing import List, Dict, Optional
import time, random, math
from enum import Enum

from src.v1.shared.models import ChainEnum
from src.v1.clustering.exceptions import InvalidAddressLength, InvalidAddressPrefix
from src.v1.clustering.constants import ADDRESS_LENGTH, HASH_LENGTH


######################################################
#                                                    #
#                   Graph Schemas                    #
#                                                    #
######################################################
class NodeType(Enum):
    holder = "holder"
    lpHolder = "lpHolder"
    smartContract = "smartContract"
    dex = "dex"
    cex = "cex"
    deployer = "deployer"


class Node(BaseModel):
    address: str
    numTokens: confloat(ge=0.0)
    percentTokens: float
    label: Optional[str] = None
    nodeType: Optional[NodeType] = NodeType.holder
    componentIndex: Optional[int] = None
    nodeValency: Optional[int] = None

    @root_validator(pre=True)
    def pre_process(cls, values):
        if not values.get('nodeType'):
            values['nodeType'] = NodeType.holder

        if values.get('address'):
            values['address'] = values['address'].lower()
        return values

    @validator('address')
    def validate_address(cls, value):
        if not value.startswith('0x'):
            raise InvalidAddressPrefix()
        if len(value) != ADDRESS_LENGTH:
            raise InvalidAddressLength()
        return value


class Transfer(BaseModel):
    fromAddress: str
    toAddress: str
    txHash: str
    token: str
    amount: float
    timestamp: int

    @root_validator(pre=True)
    def pre_process(cls, values):
        if values.get('fromAddress'):
            values['fromAddress'] = values['fromAddress'].lower()
        if values.get('toAddress'):
            values['toAddress'] = values['toAddress'].lower()
        if values.get('txHash'):
            values['txHash'] = values['txHash'].lower()
        return values

    @validator('fromAddress', 'toAddress')
    def validate_address(cls, value):
        if not value:
            return value
        if not value.startswith('0x'):
            raise InvalidAddressPrefix()
        if len(value) != ADDRESS_LENGTH:
            raise InvalidAddressLength()
        return value

    @validator('txHash')
    def validate_tx_hash(cls, value):
        if not value:
            return value
        if not value.startswith('0x'):
            raise InvalidAddressPrefix()
        if len(value) != HASH_LENGTH:
            raise InvalidAddressLength()
        return value


class Edge(BaseModel):
    fromAddress: str
    toAddress: str
    transfers: list


class Graph(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

    numNodes: int = None
    numEdges: int = None
    totalPercentage: float = None
    totalTokens: float = None

    # Calculate the lowest percentage holder in this graph
    minimumPercentage: float = None

    # Calculate concentration metrics based on the graph data
    simpsonIndex: float = None
    effectiveNumHolders: float = None

    averageHolding: float = None

    @root_validator(pre=True)
    def pre_process(cls, values):
        values['numNodes'] = len(values['nodes'])
        values['numEdges'] = len(values['edges'])

        values['simpsonIndex'] = 0

        values['totalPercentage'], values['totalTokens'] = 0, 0
        values['minimumPercentage'] = 1.0
        for node in values['nodes']:
            if isinstance(node, dict):
                if node.get('percentTokens'):
                    values['totalPercentage'] += node['percentTokens']
                    values['minimumPercentage'] = min(values['minimumPercentage'], node['percentTokens'])
                    values['simpsonIndex'] += (node['percentTokens'] ** 2)
                if node.get('numTokens'):
                    values['totalTokens'] += node['numTokens']
            elif isinstance(node, Node):
                if node.percentTokens:
                    values['totalPercentage'] += node.percentTokens
                    values['minimumPercentage'] = min(values['minimumPercentage'], node.percentTokens)
                    values['simpsonIndex'] += (node.percentTokens ** 2)
                if node.numTokens:
                    values['totalTokens'] += node.numTokens

        values['averageHolding'] = values['totalTokens'] / values['numNodes']

        if values['totalPercentage'] <= 1.0:
            values['remainder'] = 1.0 - values['totalPercentage']
            values['remainderHolders'] = math.ceil(values['remainder'] / values['minimumPercentage'])
            values['simpsonIndex'] += values['remainderHolders'] * (values['minimumPercentage'] ** 2)

        values['effectiveNumHolders'] = 1.0 / values['simpsonIndex']

        return values


class Component(BaseModel):
    nodes: List[str]
    nodePercentages: List[float]
    componentType: Optional[NodeType] = NodeType.holder

    totalPercentage: float = None
    numNodes: int = None

    @root_validator(pre=True)
    def pre_process(cls, values):
        values['numNodes'] = len(values['nodes'])

        if not values.get('componentType'):
            values['componentType'] = random.choice(["holder", "lpHolder", "smartContract", "dex", "cex", "deployer"])

        values['totalPercentage'] = 0
        for percent in values['nodePercentages']:
            values['totalPercentage'] += percent

        return values


class ClusterResponseGet(BaseModel):
    tokenAddress: str
    chain: ChainEnum
    graph: Graph
    components: Optional[List[Component]] = None

    score: int = None
    description: str = None

    timestamp: int = None
    calculationTime: float = None

    @root_validator(pre=True)
    def pre_process(cls, values):
        values['tokenAddress'] = values['tokenAddress'].lower()
        if not values.get('timestamp'):
            values['timestamp'] = int(time.time())

        effectiveNumHolders = 0
        numNodes = 0
        if isinstance(values['graph'], Graph):
            effectiveNumHolders = values['graph'].effectiveNumHolders
            numNodes = values['graph'].numNodes
        else:
            effectiveNumHolders = values['graph'].get('effectiveNumHolders')
            numNodes = values['graph'].get('numNodes')

        s = effectiveNumHolders / 10

        values['score'] = int(100 * (1 - math.exp(-s)) / (1 + math.exp(-(s - 0.1))))

        numComponents = len(values['components'])
        values['description'] = f"{numComponents} unique clusters identified in the top {numNodes} token holders."

        return values

    @validator('tokenAddress')
    def validate_address(cls, value):
        if not value.startswith('0x'):
            raise InvalidAddressPrefix()
        if len(value) != ADDRESS_LENGTH:
            raise InvalidAddressLength()
        return value
