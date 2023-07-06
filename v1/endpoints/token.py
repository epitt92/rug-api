import random
from fastapi import APIRouter, HTTPException
import time
from core.models import ContractResponse, ContractItem, TokenInfo, ScoreResponse, TokenReview
import os
import requests
import logging
from dotenv import load_dotenv
import json

load_dotenv()

mapping = None
with open('v1/utils/labels.json') as f:
    mapping = json.load(f)

router = APIRouter()

token_info = {1: {}}
contract_info = {1: {}}
score_mapping = {1: {}}
review_mapping = {1: {}}

async def post_token_last_updated(chain_id: int, token_address: str):
    if chain_id not in token_info:
        raise HTTPException(status_code=400, detail=f"Chain ID {chain_id} is not supported.")
    
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is invalid.")
    
    _token_address = token_address.lower()

    if _token_address not in token_info[chain_id]:
        raise HTTPException(status_code=404, detail=f"Token {_token_address} on chain {chain_id} has never been initialized.")

    token_info_dict = token_info[chain_id][_token_address].dict()
    token_info_dict.update(**{'lastUpdated': time.time()})
    token_info[chain_id][_token_address] = TokenInfo(**token_info_dict)

    return True

@router.get("/info/updated/{chain_id}/{token_address}")
async def get_token_last_updated(chain_id: int, token_address: str):
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
        
    if chain_id not in token_info:
        raise HTTPException(status_code=400, detail=f"Chain ID {chain_id} is not supported.")
    
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is invalid.")
    
    _token_address = token_address.lower()

    if _token_address not in token_info[chain_id]:
        raise HTTPException(status_code=404, detail=f"Token {_token_address} on chain {chain_id} has never been initialized.")
    
    return token_info[chain_id][_token_address].lastUpdated


async def initialize_token_info(chain_id: int, token_address: str):
    if chain_id not in token_info:
        raise HTTPException(status_code=400, detail=f"Chain ID {chain_id} is not supported.")
    
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is invalid.")
    
    _token_address = token_address.lower()

    if _token_address not in token_info[chain_id]:
        token_info[chain_id][_token_address] = TokenInfo()
    
    return True


async def fetch_token_socials(token_address: str):
    api_key = os.getenv('ETHERSCAN_API_KEY')

    url = 'https://api.etherscan.io/api'

    logging.info("API key: %s", api_key)

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
            raw_data['decimals'] = int(raw_data['divisor'])
            raw_data['totalSupply'] = int(raw_data['totalSupply']) / (10 ** int(raw_data['divisor']))
            raw_data['name'] = raw_data['tokenName']
            raw_data['timestamp'] = time.time()
            return raw_data
        else:
            raise HTTPException(status_code=500, detail=f"An error occurred with the Etherscan API: {data['message']}.")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"A request exception occurred: {e}.")


@router.patch("/info/{chain_id}/{token_address}", response_model=TokenInfo)
async def patch_token_info(chain_id: int, token_address: str, key: str, value: str):
    """
    Patch the token information for a given token address on a given blockchain for a specific key and value.

    The list of supported keys is as follows:

    ```['timestamp', 'name', 'symbol', 'decimals', 'total_supply', 'website', 'twitter', 'telegram', 'discord', 'circulating_supply', 'tx_count', 'holder_count', 'buy_tax', 'sell_tax', 'dex_liquidity_usd', 'deployer', 'price']```
    
    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.
    - **key** (str): The key from the above list to update.
    - **value** (str): The value to update the key at.

    __Returns:__
    - **OK**: Returns the token information as a JSON response if the call to patch the token information was successful.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the key is not part of the above list.
    - **404 Not Found**: If the token address has never been updated and does not exist.
    """
        
    if chain_id not in token_info:
        raise HTTPException(status_code=400, detail=f"Chain ID {chain_id} is not supported.")
    
    _token_address = token_address.lower()

    if _token_address not in token_info[chain_id]:
        raise HTTPException(status_code=404, detail=f"Token info for {token_address} on chain {chain_id} has never been initialized.")
    
    token_info_dict = token_info[chain_id][_token_address].dict()
    token_info_dict.update(**{key: value})
    token_info[chain_id][_token_address] = TokenInfo(**token_info_dict)

    await post_token_last_updated(chain_id, _token_address)

    return token_info[chain_id][_token_address]


@router.get("/info/{chain_id}/{token_address}", response_model=TokenInfo)
async def get_token_info(chain_id: int, token_address: str):
    """
    Get the token information for a given token address on a given blockchain.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    - **404 Not Found**: If the token address has never been updated and the token information does not exist.
    """
    if chain_id not in token_info:
        raise HTTPException(status_code=400, detail=f"Chain ID {chain_id} is not supported.")
    
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is not valid.")
    
    _token_address = token_address.lower()

    if _token_address not in token_info[chain_id]:
        raise HTTPException(status_code=404, detail=f"Token info for {_token_address} on chain {chain_id} has never been initialized.")
    
    return token_info[chain_id][_token_address]


@router.post("/info/socials/{chain_id}/{token_address}", response_model=TokenInfo)
async def post_token_socials(chain_id: int, token_address: str):
    """
    Post the token social information for a given token address on a given blockchain retrieved from an external API.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    - **500 Internal Server Error**: If an error occurred during the call to the external API.
    """

    if chain_id not in token_info:
        raise HTTPException(status_code=400, detail=f"Chain ID {chain_id} is not supported.")
    
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is not valid.")
    
    _token_address = token_address.lower()

    if _token_address not in token_info[chain_id]:
        await initialize_token_info(chain_id, _token_address)

    if token_info[chain_id][_token_address].name is None:
        try:
            info = await fetch_token_socials(_token_address)

            token_info_dict = token_info[chain_id][_token_address].dict()
            token_info_dict.update(**info)
            token_info[chain_id][_token_address] = TokenInfo(**token_info_dict)

            await post_token_last_updated(chain_id, _token_address)

            return token_info[chain_id][_token_address]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unknown error occurred during the call to fetch token info for {_token_address} on chain {chain_id}. {e}")

    return token_info[chain_id][_token_address]


@router.post("/info/price/{chain_id}/{token_address}", response_model=TokenInfo)
async def post_token_price(chain_id: int, token_address: str):
    """
    Post the latest price for a given token address on a given blockchain.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    """
    if chain_id not in token_info:
        raise HTTPException(status_code=400, detail=f"Chain ID {chain_id} is not supported.")
    
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is not valid.")
    
    _token_address = token_address.lower()

    if _token_address not in token_info[chain_id]:
        await initialize_token_info(chain_id, _token_address)
    
    if token_info[chain_id][_token_address].latestPrice is None:
        price = float(random.randint(0, 10000) / 10000)
        await patch_token_info(chain_id, _token_address, 'latestPrice', price)

    return token_info[chain_id][_token_address]


@router.post("/info/liquidity/{chain_id}/{token_address}", response_model=TokenInfo)
async def post_token_liquidity_info(chain_id: int, token_address: str):
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
    if chain_id not in token_info:
        raise HTTPException(status_code=400, detail=f"Chain ID {chain_id} is not supported.")
    
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is not valid.")
    
    _token_address = token_address.lower()

    if _token_address not in token_info[chain_id]:
        await initialize_token_info(chain_id, _token_address)

    if token_info[chain_id][_token_address].deployer is None:
        try:
            url = 'https://api.gopluslabs.io/api/v1/token_security/1'

            params = {
                'contract_addresses': _token_address
            }

            request_response = requests.get(url, params=params)
            request_response.raise_for_status()
            
            if request_response.status_code == 200:
                data = request_response.json()

                await patch_token_info(chain_id, _token_address, 'deployer', data['result'][_token_address]['creator_address'])
                await patch_token_info(chain_id, _token_address, 'holders', int(data['result'][_token_address]['holder_count']))
                await patch_token_info(chain_id, _token_address, 'buyTax', float(data['result'][_token_address]['buy_tax']))
                await patch_token_info(chain_id, _token_address, 'sellTax', float(data['result'][_token_address]['sell_tax']))
                await patch_token_info(chain_id, _token_address, 'liquidityUsd', sum([float(item['liquidity']) for item in data['result'][_token_address]['dex']]))
            else:
                raise HTTPException(status_code=500, detail=f"An unknown error occurred during the call to fetch token security information for {_token_address} on chain {chain_id}.")

            await post_token_last_updated(chain_id, _token_address)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unknown error occurred during the call to fetch token security information for {_token_address} on chain {chain_id}. {e}")
    
    return token_info[chain_id][_token_address]


@router.post("/info/{chain_id}/{token_address}", response_model=TokenInfo)
async def post_token_info(chain_id: int, token_address: str):
    """
    Post the latest information for a given token address on a given blockchain.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    """
    if chain_id not in token_info:
        raise HTTPException(status_code=400, detail=f"Chain ID {chain_id} is not supported.")
    
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is not valid.")
    
    _token_address = token_address.lower()

    if _token_address not in token_info[chain_id]:
        await initialize_token_info(chain_id, _token_address)

    if token_info[chain_id][_token_address].name is None:
        await post_token_socials(chain_id, _token_address)
    
    await post_token_liquidity_info(chain_id, _token_address)
    await post_token_price(chain_id, _token_address)

    return token_info[chain_id][_token_address]


@router.post("/contract/{chain_id}/{token_address}", response_model=ContractResponse)
async def post_token_contract_info(chain_id: int, token_address: str):
    """
    Fetches the contract information for a given token address on a given blockchain.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    """
    if chain_id not in contract_info:
        raise HTTPException(status_code=400, detail=f"Chain ID {chain_id} is not supported.")
    
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is not valid.")
    
    if mapping is None:
        raise HTTPException(status_code=500, detail=f"Failed to load labels from static file.")
    
    _token_address = token_address.lower()

    if _token_address not in contract_info[chain_id]:
        try:
            url = 'https://api.gopluslabs.io/api/v1/token_security/1'

            params = {
                'contract_addresses': _token_address
            }

            request_response = requests.get(url, params=params)
            request_response.raise_for_status()
            
            if request_response.status_code == 200:
                data = request_response.json()

                data_response = data['result'][_token_address]

                items = []

                for key, item in mapping.items():
                    if key in data_response:
                        item = ContractItem(
                            title=item['title'],
                            section=item['section'],
                            generalDescription=item['description'],
                            description=item['false_description'] if bool(data_response[key]) else item['true_description'],
                            value=float(data_response[key]) if data_response[key] != '' else None,
                            severity=item['severity']
                        )

                        items.append(item)

                contract_info[chain_id][_token_address] = ContractResponse(items=items)
            else:
                raise HTTPException(status_code=500, detail=f"Failed to fetch token security information from GoPlus: {request_response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch token security information from GoPlus: {e}")

    return contract_info[chain_id][_token_address]

@router.post("/score/{chain_id}/{token_address}", response_model=ScoreResponse)
async def post_score_info(chain_id: int, token_address: str):
    if chain_id not in score_mapping:
        raise HTTPException(status_code=400, detail=f"Chain ID {chain_id} is not supported.")
    
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is not valid.")
    
    _token_address = token_address.lower()

    if _token_address not in score_mapping[chain_id]:
        score_mapping[chain_id][_token_address] = {"overallScore": int(random.randint(0, 100)), "liquidityScore": int(random.randint(0, 100)), "transferrabilityScore": int(random.randint(0, 100)), "supplyScore": int(random.randint(0, 100))}
    
    return score_mapping[chain_id][_token_address]

@router.post("/review/{chain_id}/{token_address}", response_model=TokenReview)
async def post_token_review(chain_id: int, token_address: str):
    score = await post_score_info(chain_id, token_address)
    token_info = await post_token_info(chain_id, token_address)
    contract_info = await post_token_contract_info(chain_id, token_address)

    return TokenReview(tokenInfo=token_info, score=score, contractInfo=contract_info)
