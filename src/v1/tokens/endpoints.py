from fastapi import APIRouter, HTTPException
import time, os, requests, json
from dotenv import load_dotenv

import logging

from src.v1.shared.dependencies import get_random_score
from src.v1.shared.constants import CHAIN_ID_MAPPING, ETHEREUM_CHAIN_ID
from src.v1.shared.models import ChainEnum
from src.v1.shared.schemas import Chain
from src.v1.shared.exceptions import validate_token_address
from src.v1.tokens.constants import CLUSTER_RESPONSE, AI_SUMMARY_DESCRIPTION, AI_COMMENTS, AI_SCORE, BURN_TAG
from src.v1.tokens.dependencies import get_supply_summary, get_transferrability_summary
from src.v1.tokens.schemas import TokenInfoResponse, TokenReviewResponse, TokenMetadata, ContractResponse, ContractItem, AISummary, ClusterResponse
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

token_metadata = {'ethereum': {}}
token_ai_summary = {'ethereum': {}}
supply_info = {'ethereum': {}}
transferrability_info = {'ethereum': {}}
score_mapping = {'ethereum': {}}
review_mapping = {'ethereum': {}}

async def patch_token_metadata(chain: ChainEnum, token_address: str, updateKey: TokenMetadataEnum, updateValue):    
    _token_address = token_address.lower()

    if _token_address not in token_metadata[chain.value]:
        await initialize_token_metadata(chain, _token_address)
    
    token_info_dict = token_metadata[chain.value][_token_address].dict()
    token_info_dict.update(**{updateKey: updateValue})
    token_metadata[chain.value][_token_address] = TokenMetadata(**token_info_dict)

    return token_metadata[chain.value][_token_address]


@router.get("/info/updated/{chain}/{token_address}")
async def get_token_last_updated(chain: ChainEnum, token_address: str):
    """
    Retrieve the UNIX timestamp at which a token was last updated.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Returns:__
    - **OK**: Returns the last updated UNIX timestamp as a JSON response.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    - **404 Not Found**: If the token address has never been updated.
    """
    validate_token_address(token_address)
    _token_address = token_address.lower()

    if _token_address not in token_metadata[chain.value]:
        raise HTTPException(status_code=404, detail=f"Token {_token_address} on chain {chain} has never been initialized.")
    
    return token_metadata[chain.value][_token_address].lastUpdatedTimestamp


async def initialize_token_metadata(chain: ChainEnum, token_address: str):
    validate_token_address(token_address)
    _token_address = token_address.lower()

    if _token_address not in token_metadata[chain.value]:
        data = await get_block_explorer_data(_token_address)
        token_metadata[chain.value][_token_address] = TokenMetadata(name=data.get("name"), symbol=data.get("symbol"), chain=Chain(chainId=CHAIN_ID_MAPPING[chain.value]), tokenAddress=_token_address)
    
    return token_metadata[chain.value][_token_address]


@router.get("/explorer_data/{token_address}", include_in_schema=False)
async def get_block_explorer_data(token_address: str):
    api_key = os.getenv('ETHERSCAN_API_KEY')

    url = 'https://api.etherscan.io/api'

    params = {
        'module': 'token',
        'action': 'tokeninfo',
        'contractaddress': token_address,
        'apikey': api_key
    }

    try:
        result = requests.get(url, params=params)
        result.raise_for_status()
        data = result.json()

        if data['status'] == "1":
            raw_data = data['result'][0]

            output = {}
            output['name'] = raw_data['tokenName']
            output['symbol'] = raw_data['symbol']
            output['decimals'] = int(raw_data['divisor'])
            output['totalSupply'] = int(raw_data['totalSupply']) / (10 ** int(raw_data['divisor']))

            # TODO: Temporarily make circulating supply the same as total supply
            output['circulatingSupply'] = output['totalSupply']
            output['totalSupplyPercentage'] = 1.0

            output['website'] = raw_data['website'] if raw_data['website'] != '' else None
            output['twitter'] = raw_data['twitter'] if raw_data['twitter'] != '' else None
            output['telegram'] = raw_data['telegram'] if raw_data['telegram'] != '' else None
            output['discord'] = raw_data['discord'] if raw_data['discord'] != '' else None

            return output
        else:
            raise HTTPException(status_code=500, detail=f"An error occurred with the Etherscan API: {data['message']}.")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"A request exception occurred: {e}.")


async def token_metadata_check(chain: ChainEnum, token_address: str):
    _token_address = token_address.lower()

    metadata = token_metadata[chain.value].get(_token_address)

    if not metadata:
        await initialize_token_metadata(chain, _token_address)
    
    return token_metadata[chain.value].get(_token_address)


@router.get("socials/{chain}/{token_address}", response_model=TokenMetadata, include_in_schema=False)
async def post_token_socials(chain: ChainEnum, token_address: str):
    """
    Post the token social information for a given token address on a given blockchain retrieved from an external API.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.
    """
    validate_token_address(token_address)
    _token_address = token_address.lower()

    metadata = await token_metadata_check(chain, _token_address)

    if (metadata.twitter is None):
        try:
            info = await get_block_explorer_data(_token_address)

            for key, value in info.items():
                await patch_token_metadata(chain, _token_address, key, value)

            await patch_token_metadata(chain, _token_address, 'lastUpdatedTimestamp', int(time.time()))

            return token_metadata[chain.value][_token_address]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unknown error occurred during the call to fetch token info for {_token_address} on chain {chain.value}")

    return token_metadata[chain.value][_token_address]


@router.get("liquidity/{chain}/{token_address}", response_model=TokenMetadata, include_in_schema=False)
async def post_token_liquidity_info(chain: ChainEnum, token_address: str):
    """
    Post the latest liquidity information for a given token address on a given blockchain. This information is queried directly from GoPlus Labs endpoints for token contract security.

    This endpoint will update the following entries:
    - **dex_liquidity_usd**: The latest liquidity information for the token.
    - **buy_tax**: The latest buy tax information for the token.
    - **sell_tax**: The latest sell tax information for the token.
    - **deployer**: The address of the deployer of the token contract.
    - **holder_count**: The number of holders of the token contract.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    """
    validate_token_address(token_address)
    _token_address = token_address.lower()

    metadata = await token_metadata_check(chain, _token_address)

    if metadata.contractDeployer is None:
        try:
            url = f'https://api.gopluslabs.io/api/v1/token_security/{CHAIN_ID_MAPPING[chain.value]}'

            params = {
                'contract_addresses': _token_address
            }

            request_response = requests.get(url, params=params)
            request_response.raise_for_status()
            
            if request_response.status_code == 200:
                data = request_response.json()

                await patch_token_metadata(chain, _token_address, 'contractDeployer', data['result'][_token_address]['creator_address'])
                await patch_token_metadata(chain, _token_address, 'holders', int(data['result'][_token_address]['holder_count']))
                await patch_token_metadata(chain, _token_address, 'buyTax', float(data['result'][_token_address]['buy_tax']))
                await patch_token_metadata(chain, _token_address, 'sellTax', float(data['result'][_token_address]['sell_tax']))

                # Liquidity token calculations
                liquidityUsd = sum([float(item['liquidity']) for item in data['result'][_token_address]['dex']])

                # Locked and burned liquidity calculations
                lp_holders = data['result'][_token_address]['lp_holders']

                lockedLiquidity, burnedLiquidity = 0.0, 0.0
                for lp in lp_holders:
                    if lp.get('percent'):
                        percent = float(lp.get('percent'))
                        if lp.get("tag") == BURN_TAG:
                            burnedLiquidity += percent
                        elif lp.get("is_locked") == 1:
                            lockedLiquidity += float(lp.get('percent'))

                await patch_token_metadata(chain, _token_address, 'liquidityUsd', liquidityUsd)
                if lockedLiquidity > 0.001:
                    await patch_token_metadata(chain, _token_address, 'lockedLiquidity', lockedLiquidity)
                if burnedLiquidity > 0.001:
                    await patch_token_metadata(chain, _token_address, 'burnedLiquidity', burnedLiquidity)
            else:
                raise HTTPException(status_code=500, detail=f"An unknown error occurred during the call to fetch token security information for {_token_address} on chain {chain}.")

            await patch_token_metadata(chain, _token_address, 'lastUpdatedTimestamp', time.time())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unknown error occurred during the call to fetch token security information for {_token_address} on chain {chain}. {e}")
    
    return token_metadata[chain.value][_token_address]


@router.get("logo/{chain}/{token_address}", response_model=TokenMetadata, include_in_schema=False)
async def post_token_logo_info(chain: ChainEnum, token_address: str):
    validate_token_address(token_address)
    _token_address = token_address.lower()

    metadata = await token_metadata_check(chain, _token_address)

    if metadata.logoUrl is None:
        if tokens.get(_token_address):
            await patch_token_metadata(chain, _token_address, 'logoUrl', tokens[_token_address]['logoUrl'])

        # TODO: Add link to randomly generated rug.ai icon
    return token_metadata[chain.value][_token_address]


async def post_token_contract_info(chain: ChainEnum, token_address: str):
    """
    Fetches the contract information for a given token address on a given blockchain.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    """
    validate_token_address(token_address)

    if mapping is None:
        raise HTTPException(status_code=500, detail=f"Failed to load labels from static file.")
    
    _token_address = token_address.lower()

    if (_token_address not in supply_info[chain.value]) or (_token_address not in transferrability_info[chain.value]):
        try:
            url = f'https://api.gopluslabs.io/api/v1/token_security/{CHAIN_ID_MAPPING[chain.value]}'

            params = {
                'contract_addresses': _token_address
            }

            request_response = requests.get(url, params=params)
            request_response.raise_for_status()
            
            if request_response.status_code == 200:
                data = request_response.json()

                data_response = data['result'][_token_address]

                # Process this data and produce a supply and a transferrability summary
                supply_summary = get_supply_summary(data_response)
                transferrability_summary = get_transferrability_summary(data_response)

                supply_info[chain.value][_token_address] = supply_summary
                transferrability_info[chain.value][_token_address] = transferrability_summary

                return supply_summary, transferrability_summary
            else:
                raise HTTPException(status_code=500, detail=f"Failed to fetch token security information from GoPlus: {request_response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch token security information from GoPlus: {e}")

    return supply_info[chain.value][_token_address], transferrability_info[chain.value][_token_address]


async def post_token_score(chain: ChainEnum, token_address: str):
    validate_token_address(token_address)
    _token_address = token_address.lower()

    if _token_address not in score_mapping[chain.value]:
        score_mapping[chain.value][_token_address] = get_random_score()

    return score_mapping[chain.value][_token_address]


async def post_token_metadata(chain: ChainEnum, token_address: str):
    validate_token_address(token_address)
    _token_address = token_address.lower()

    if _token_address not in token_metadata[chain.value]:
        await initialize_token_metadata(chain, _token_address)

    await post_token_socials(chain, _token_address)
    await post_token_liquidity_info(chain, _token_address)
    await post_token_logo_info(chain, _token_address)

    chart = await get_chart_data(chain, _token_address, FrequencyEnum('1d'))

    # Patch latest price and add 24h volume
    await patch_token_metadata(chain, _token_address, 'latestPrice', chart.latestPrice)
    await patch_token_metadata(chain, _token_address, 'volume24h', chart.dayVolume)

    return token_metadata[chain.value][_token_address]


@router.get("/ai/{chain}/{token_address}", response_model=AISummary, include_in_schema=False)
async def get_token_ai_summary(chain: ChainEnum, token_address: str):
    validate_token_address(token_address)
    _token_address = token_address.lower()

    if _token_address not in token_ai_summary[chain.value]:
        # TODO: Wire this up to the rug-ml API as a request
        aiSummary = AISummary(description=AI_SUMMARY_DESCRIPTION, numIssues=7, overallScore=AI_SCORE, comments=AI_COMMENTS)
        token_ai_summary[chain.value][_token_address] = aiSummary

    return token_ai_summary[chain.value][_token_address]


@router.get("/cluster/{chain}/{token_address}", response_model=ClusterResponse, include_in_schema=False)
async def get_token_cluster_summary(chain: ChainEnum, token_address: str):
    validate_token_address(token_address)
    return CLUSTER_RESPONSE


async def post_token_info(chain: ChainEnum, token_address: str):
    """
    Post the latest information for a given token address on a given blockchain.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    """
    validate_token_address(token_address)
    _token_address = token_address.lower()

    tokenMetadata = await post_token_metadata(chain, token_address)
    score = await post_token_score(chain, _token_address)
    ai_summary = await get_token_ai_summary(chain, _token_address)
    topHolders = await get_token_cluster_summary(chain, _token_address)

    return TokenInfoResponse(tokenSummary=tokenMetadata, score=score, contractSummary=ai_summary, holderChart=topHolders)


@router.get("/info/{chain}/{token_address}", response_model=TokenInfoResponse)
async def get_token_info(chain: ChainEnum, token_address: str):
    validate_token_address(token_address)
    _token_address = token_address.lower()
    return await post_token_info(chain, _token_address)


@router.get("/review/{chain}/{token_address}", response_model=TokenReviewResponse)
async def get_token_detailed_review(chain: ChainEnum, token_address: str): 
    validate_token_address(token_address)

    token_info = await post_token_info(chain, token_address)

    supplySummary, transferrabilitySummary = await post_token_contract_info(chain, token_address)
    # liquiditySummary = await get_token_cluster_summary(chain, token_address)
    sourceCode = await get_source_code(chain, token_address)

    return TokenReviewResponse(tokenSummary=token_info.tokenSummary, 
                               score=token_info.score, 
                               contractSummary=token_info.contractSummary, 
                               holderChart=token_info.holderChart, 
                               supplySummary=supplySummary, 
                               transferrabilitySummary=transferrabilitySummary, 
                               liquiditySummary=None, 
                               sourceCode=sourceCode)
