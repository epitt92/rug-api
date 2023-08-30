from fastapi import APIRouter, HTTPException
import time, os, requests, json, logging, math
from dotenv import load_dotenv
from decimal import Decimal

from src.v1.shared.dependencies import get_random_score, get_primary_key, get_chain
from src.v1.shared.constants import CHAIN_ID_MAPPING, ETHEREUM_CHAIN_ID
from src.v1.shared.models import ChainEnum
from src.v1.shared.schemas import Chain, ScoreResponse, Score
from src.v1.shared.exceptions import validate_token_address
from src.v1.shared.DAO import DAO

from src.v1.tokens.constants import SUPPLY_REPORT_STALENESS_THRESHOLD, TRANSFERRABILITY_REPORT_STALENESS_THRESHOLD, TOKEN_METRICS_STALENESS_THRESHOLD
from src.v1.tokens.dependencies import get_supply_summary, get_transferrability_summary
from src.v1.tokens.dependencies import get_go_plus_summary, get_block_explorer_data, get_go_plus_data
from src.v1.tokens.schemas import Holder, Cluster, ClusterResponse, AIComment, AISummary, TokenInfoResponse, TokenReviewResponse, TokenMetadata, ContractResponse, ContractItem, AISummary
from src.v1.tokens.models import TokenMetadataEnum

from src.v1.sourcecode.endpoints import get_source_code

from src.v1.chart.endpoints import get_chart_data
from src.v1.chart.models import FrequencyEnum
from src.v1.chart.schemas import ChartResponse

load_dotenv()

mapping = None
with open('src/v1/tokens/files/labels.json') as f:
    mapping = json.load(f)

tokens = None
with open('src/v1/shared/files/tokens.json') as f:
    tokens = json.load(f)["tokens"]

ETHEREUM = Chain(chainId=ETHEREUM_CHAIN_ID)

router = APIRouter()

SUPPLY_REPORT_DAO = DAO("supplyreports")
TRANSFERRABILITY_REPORT_DAO = DAO("transferrabilityreports")
TOKEN_METRICS_DAO = DAO("tokenmetrics")

@router.get("info/{chain}/{token_address}", include_in_schema=True)
async def get_supply_transferrability_info(chain: ChainEnum, token_address: str):
    validate_token_address(token_address)

    if mapping is None:
        raise HTTPException(status_code=500, detail=f"Failed to load labels from static file.")
    
    _token_address = token_address.lower()
    
    pk = get_primary_key(_token_address, chain)

    # Add a DAO check for both supply and transferrability summary
    _supply_summary = SUPPLY_REPORT_DAO.find_most_recent_by_pk(pk)
    _transferrability_summary = TRANSFERRABILITY_REPORT_DAO.find_most_recent_by_pk(pk)

    found = False

    # If this data is found and is not stale, return it
    if _supply_summary and _transferrability_summary:
        if (time.time() - int(_supply_summary.get('timestamp'))) < SUPPLY_REPORT_STALENESS_THRESHOLD and (time.time() - int(_transferrability_summary.get('timestamp'))) < TRANSFERRABILITY_REPORT_STALENESS_THRESHOLD:
            found = True
            supply_summary = _supply_summary.get('summary')
            transferrability_summary = _transferrability_summary.get('summary')
    
    if not found:
        data = get_go_plus_data(chain, _token_address)

        # Process this data and produce a supply and a transferrability summary
        supply_summary = get_supply_summary(data)
        transferrability_summary = get_transferrability_summary(data)

        # Cache this data to the database
        SUPPLY_REPORT_DAO.insert_one(partition_key_value=pk, item={'timestamp': int(time.time()), 'summary': dict(supply_summary)})
        # TRANSFERRABILITY_REPORT_DAO.insert_one(partition_key_value=pk, item={'timestamp': int(time.time()), 'summary': dict(transferrability_summary)})

    # Format the data and return it
    supply_summary = ContractResponse(items=supply_summary.get("items"), score=supply_summary.get("score"), description=supply_summary.get("summary"))
    transferrability_summary = ContractResponse(items=transferrability_summary.get("items"), score=transferrability_summary.get("score"), description=transferrability_summary.get("summary"))

    return supply_summary, transferrability_summary

@router.get("/metadata/{chain}/{token_address}", include_in_schema=True)
async def get_token_metrics(chain: ChainEnum, token_address: str):
    validate_token_address(token_address)
    _token_address = token_address.lower()

    pk = get_primary_key(_token_address, chain)

    # Add a DAO check for both supply and transferrability summary
    _token_metrics = TOKEN_METRICS_DAO.find_most_recent_by_pk(pk)
    found = False

    if _token_metrics:
        token_metrics_last_updated = _token_metrics.get('timestamp')

        if ((time.time() - int(token_metrics_last_updated)) < TOKEN_METRICS_STALENESS_THRESHOLD):
            found = True
    
    if not found:
        # Fetch the data from all sources and then cache it in the database
        lastUpdatedTimestamp = int(time.time())

        # Fetch and process market data from GoPlus
        market_data = get_go_plus_summary(chain, _token_address)

        # Fetch and process token social data from Etherscan
        try:
            explorer_data = get_block_explorer_data(chain, _token_address)
        except Exception as e:
            logging.warning(f'Failed to fetch block explorer data for {_token_address} on chain {chain}. Using empty dictionary and continuing...')
            explorer_data = {}

        try:
            # Fetch latestPrice information from chart data
            chart = await get_chart_data(chain, _token_address, FrequencyEnum.one_day)
            if chart:
                market_data['latestPrice'] = chart.latestPrice if isinstance(chart, ChartResponse) else chart.get('latestPrice')
        except Exception as e:
            logging.warning(f'Failed to fetch chart data as part of `info` for {_token_address} on chain {chain}. Using empty dictionary and continuing...')
            market_data['latestPrice'] = None

        # TODO: Add support for calling name and symbol from RPC directly as a fallback
        
        _token_metrics = {
            'timestamp': lastUpdatedTimestamp,
            'summary': {
                **market_data,
                **explorer_data
            }
        }

        # Change floating point fields in the token metrics to Decimal type
        for key in _token_metrics['summary']:
            if isinstance(_token_metrics['summary'][key], float):
                _token_metrics['summary'][key] = Decimal(str(_token_metrics['summary'][key]))

        TOKEN_METRICS_DAO.insert_one(partition_key_value=pk, item=_token_metrics)

    _token_metrics = {
        **_token_metrics['summary'],
        **{
            'tokenAddress': _token_address,
            'chain': get_chain(chain)
        }
    }

    return TokenMetadata(**_token_metrics)


@router.get("/audit/{chain}/{token_address}", include_in_schema=True)
async def get_token_audit_summary(chain: ChainEnum, token_address: str):
    validate_token_address(token_address)
    _token_address = token_address.lower()

    # TODO: Add support for multiple chains to this analysis
    _chain = str(chain.value) if isinstance(chain, ChainEnum) else str(chain)
    URL = os.environ.get('ML_API_URL') + f'/v1/audit/{_chain}/{token_address.lower()}'

    response = requests.get(URL)
    response.raise_for_status()

    data = response.json().get("data")

    if data:
        description = data.get("tokenSummary")

        if not data.get('tokenScore') and not data.get('filesResult'):
            raise HTTPException(status_code=500, detail=f"Failed to fetch AI data for {_token_address} on chain {chain.value}: {description}")

        overallScore = float(data.get("tokenScore"))

        files = data.get("filesResult")

        numIssues = sum([len(item.get("result")) for item in files])

        comments = []
        for smart_contract in files:
            for issue in smart_contract.get("result"):
                lines = issue.get("lines")

                if lines:
                    lines = [int(item) for item in lines]

                comment = AIComment(
                    commentType="Function",
                    title=issue.get("title"),
                    description=issue.get("description"),
                    severity=issue.get("level"),
                    fileName=smart_contract.get("fileName"),
                    sourceCode=issue.get("function_code"),
                    lines=lines
                )
                comments.append(comment)
    else:
        return None

    return AISummary(description=description, numIssues=numIssues, overallScore=overallScore, comments=comments)


@router.get("/cluster/{chain}/{token_address}", include_in_schema=True)
async def get_token_clustering(chain: ChainEnum, token_address: str):
    validate_token_address(token_address)

    URL = os.environ.get('ML_API_URL') + f'/v1/clustering/{chain.value}/{token_address.lower()}'

    try:
        response = requests.get(URL)
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch clustering data for {token_address} on chain {chain.value}: {e}")

    return response.json()
    

@router.get("/holderchart/{chain}/{token_address}", response_model=ClusterResponse, include_in_schema=True)
async def get_holder_chart(chain: ChainEnum, token_address: str, numClusters: int = 10):
    validate_token_address(token_address)

    URL = os.environ.get('ML_API_URL') + f'/v1/clustering/holders/{chain.value}/{token_address.lower()}'

    try:
        response = requests.get(URL)
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch holder data for {token_address} on chain {chain.value}: {e}")

    data = response.json()
    top_holders = sorted(data.keys(), key=lambda k: data[k]["numTokens"], reverse=True)[:numClusters]

    holders = {holder: data[holder] for holder in top_holders}

    clusters = [Cluster(members=[Holder(address=holder, numTokens=float(holders[holder]["numTokens"]), percentage=float(holders[holder]["percentTokens"]))]) for holder in holders]
    
    return ClusterResponse(clusters=clusters)


@router.get("/score/{chain}/{token_address}", response_model=ScoreResponse, include_in_schema=True)
async def get_score_info(chain: ChainEnum, token_address: str):
    supplySummary, transferrabilitySummary = await get_supply_transferrability_info(chain, token_address)

    supplyScore = Score(value=supplySummary.score, description=supplySummary.description)
    transferrabilityScore = Score(value=transferrabilitySummary.score, description=transferrabilitySummary.description)

    score = ScoreResponse(overallScore=math.sqrt(supplyScore.value * transferrabilityScore.value), supplyScore=supplyScore, transferrabilityScore=transferrabilityScore)
    return score


@router.get("/info/{chain}/{token_address}", response_model=TokenInfoResponse)
async def get_token_info(chain: ChainEnum, token_address: str):
    validate_token_address(token_address)
    
    tokenSummary = await get_token_metrics(chain, token_address)

    score = await get_score_info(chain, token_address)
    
    holderChart = await get_holder_chart(chain, token_address)

    return TokenInfoResponse(tokenSummary=tokenSummary, score=score, holderChart=holderChart)


@router.get("/review/{chain}/{token_address}", response_model=TokenReviewResponse)
async def get_token_detailed_review(chain: ChainEnum, token_address: str): 
    validate_token_address(token_address)

    # Get the supply and transferrability summary information
    supplySummary, transferrabilitySummary = await get_supply_transferrability_info(chain, token_address)

    # Get and cache the source code for the token
    sourceCode = await get_source_code(chain, token_address)

    # Get the token summary for the token
    token_info = await get_token_info(chain, token_address)

    return TokenReviewResponse(tokenSummary=token_info.tokenSummary, 
                               score=token_info.score, 
                               holderChart=token_info.holderChart, 
                               supplySummary=supplySummary, 
                               transferrabilitySummary=transferrabilitySummary, 
                               sourceCode=sourceCode)
