from fastapi import APIRouter, HTTPException
import time, os, requests, json, logging
from dotenv import load_dotenv
from decimal import Decimal

from src.v1.shared.dependencies import get_random_score, get_primary_key, get_chain
from src.v1.shared.constants import CHAIN_ID_MAPPING, ETHEREUM_CHAIN_ID
from src.v1.shared.models import ChainEnum
from src.v1.shared.schemas import Chain, ScoreResponse
from src.v1.shared.exceptions import validate_token_address
from src.v1.shared.DAO import DAO
from src.v1.tokens.constants import CLUSTER_RESPONSE, AI_SUMMARY_DESCRIPTION, AI_COMMENTS, AI_SCORE, BURN_TAG
from src.v1.tokens.constants import SUPPLY_REPORT_STALENESS_THRESHOLD, TRANSFERRABILITY_REPORT_STALENESS_THRESHOLD, TOKEN_METRICS_STALENESS_THRESHOLD
from src.v1.tokens.dependencies import get_supply_summary, get_transferrability_summary
from src.v1.tokens.dependencies import get_go_plus_summary, get_block_explorer_data, get_go_plus_data
from src.v1.tokens.schemas import AIComment, AISummary, TokenInfoResponse, TokenReviewResponse, TokenMetadata, ContractResponse, ContractItem, AISummary, ClusterResponse
from src.v1.tokens.models import TokenMetadataEnum
from src.v1.sourcecode.endpoints import get_source_code
from src.v1.chart.endpoints import get_chart_data
from src.v1.chart.models import FrequencyEnum

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
            logging.info(f"Supply and transferrability summary found for {_token_address} on chain {chain.value} in DynamoDB")
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
        TRANSFERRABILITY_REPORT_DAO.insert_one(partition_key_value=pk, item={'timestamp': int(time.time()), 'summary': dict(transferrability_summary)})

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
            logging.info(f"Token metrics found for {_token_address} on chain {chain.value} in DynamoDB")
            found = True
    
    if not found:
        # Fetch the data from all sources and then cache it in the database
        lastUpdatedTimestamp = int(time.time())

        # Fetch and process market data from GoPlus
        market_data = get_go_plus_summary(chain, _token_address)

        # Fetch and process token social data from Etherscan
        explorer_data = get_block_explorer_data(chain, _token_address)

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

        logging.info(f'Caching token metrics for {_token_address} on chain {chain.value} in DynamoDB')
        logging.info(f'Token metrics: {_token_metrics}')

        TOKEN_METRICS_DAO.insert_one(partition_key_value=pk, item=_token_metrics)

    _token_metrics = {
        **_token_metrics['summary'],
        **{
            'tokenAddress': _token_address,
            'chain': get_chain(chain)
        }
    }

    return TokenMetadata(**_token_metrics)

@router.get("/ai/{chain}/{token_address}", include_in_schema=True)
async def get_token_audit_summary(chain: ChainEnum, token_address: str):
    validate_token_address(token_address)
    _token_address = token_address.lower()

    # TODO: Add support for multiple chains to this analysis
    URL = os.environ.get('ML_API_URL') + f'/v1/audit/token_scan/{token_address.lower()}'

    response = requests.get(URL)
    response.raise_for_status()

    data = response.json().get("data")

    if data:
        description = data.get("tokenSummary")
        overallScore = float(data.get("tokenScore"))

        files = data.get("filesResult")

        numIssues = sum([len(item.get("result")) for item in files])

        comments = []
        for smart_contract in files:
            for issue in smart_contract.get("result"):
                comment = AIComment(
                    commentType="Function",
                    title=issue.get("title"),
                    description=issue.get("description"),
                    severity=issue.get("level"),
                    fileName=smart_contract.get("fileName"),
                    sourceCode=smart_contract.get("sourceCode")
                )
                comments.append(comment)
    else:
        return None

    return AISummary(description=description, numIssues=numIssues, overallScore=overallScore, comments=comments)


@router.get("/cluster/{chain}/{token_address}", response_model=ClusterResponse, include_in_schema=True)
async def get_token_clustering(chain: ChainEnum, token_address: str):
    validate_token_address(token_address)

    URL = os.environ.get('DEV_ML_API_URL') + f'/v1/clustering/{chain.value}/{token_address.lower()}'

    response = requests.get(URL)
    response.raise_for_status()

    CLUSTER_RESPONSE = ClusterResponse(**response.json())
    
    return CLUSTER_RESPONSE


@router.get("/info/{chain}/{token_address}", response_model=TokenInfoResponse)
async def get_token_info(chain: ChainEnum, token_address: str):
    validate_token_address(token_address)
    _token_address = token_address.lower()
    
    tokenMetadata = await get_token_metrics(chain, token_address)

    # Get the AI summary for the token
    _AISummary = await get_token_audit_summary(chain, token_address)
    
    score = None

    topHolders = None

    return TokenInfoResponse(tokenSummary=tokenMetadata, score=score, contractSummary=_AISummary, holderChart=topHolders)


@router.get("/review/{chain}/{token_address}", response_model=TokenReviewResponse)
async def get_token_detailed_review(chain: ChainEnum, token_address: str): 
    validate_token_address(token_address)

    # Get the supply and transferrability summary information
    supplySummary, transferrabilitySummary = await get_supply_transferrability_info(chain, token_address)

    # Get the clustering report for the token
    liquiditySummary = None

    # Get and cache the source code for the token
    sourceCode = await get_source_code(chain, token_address)

    # Get the token summary for the token
    token_info = await get_token_info(chain, token_address)

    return TokenReviewResponse(tokenSummary=token_info.tokenSummary, 
                               score=token_info.score, 
                               contractSummary=token_info.contractSummary, 
                               holderChart=token_info.holderChart, 
                               supplySummary=supplySummary, 
                               transferrabilitySummary=transferrabilitySummary, 
                               liquiditySummary=liquiditySummary, 
                               sourceCode=sourceCode)
