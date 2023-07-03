from fastapi import HTTPException
from fastapi import APIRouter, HTTPException, Query
import time
from pydantic import Field
import time
from core.models import success, error, response
import os
import requests
import logging
import random
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

token_info = {1: {}}

INFO_KEYS = ['timestamp', 'name', 'symbol', 'decimals', 'total_supply', 'website', 'twitter', 'telegram', 'discord', 'circulating_supply', 'tx_count', 'holder_count', 'buy_tax', 'sell_tax', 'dex_liquidity_usd', 'deployer', 'price']

async def post_token_last_updated(chain_id: int, token_address: str):
    if chain_id not in token_info:
        raise HTTPException(status_code=400, detail=f"Chain ID {chain_id} is not supported.")
    
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is invalid.")
    
    _token_address = token_address.lower()

    if _token_address not in token_info[chain_id]:
        raise HTTPException(status_code=404, detail=f"Token {_token_address} on chain {chain_id} has never been initialized.")

    token_info[chain_id][_token_address]['timestamp'] = int(time.time())
    return success(f"Token {_token_address} on chain {chain_id} was updated at {token_info[chain_id][_token_address]['timestamp']}.")


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
    
    return response({'timestamp': token_info[chain_id][_token_address]['timestamp']})


async def initialize_token_info(chain_id: int, token_address: str):
    if chain_id not in token_info:
        raise HTTPException(status_code=400, detail=f"Chain ID {chain_id} is not supported.")
    
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is invalid.")
    
    _token_address = token_address.lower()

    if _token_address not in token_info[chain_id]:
        token_info[chain_id][_token_address] = {key: None for key in INFO_KEYS}
    
    return success(f"Token info for {_token_address} on chain {chain_id} was initialized.")


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
            raw_data['total_supply'] = int(raw_data['totalSupply']) / (10 ** int(raw_data['divisor']))
            raw_data['name'] = raw_data['tokenName']
            raw_data['timestamp'] = time.time()

            key_overlap = set(raw_data.keys()).intersection(set(INFO_KEYS))
            return response({key: raw_data[key] if raw_data[key] != "" else None for key in key_overlap})
        else:
            return error(f"An external API response error occurred with message: {data['message']}")
    except requests.exceptions.RequestException as e:
        return error(f"A request exception occurred with error: {e}.")


@router.patch("/info/{chain_id}/{token_address}")
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
    
    if key not in INFO_KEYS:
        raise HTTPException(status_code=400, detail=f"Entry {key} is not supported.")
    
    _token_address = token_address.lower()

    if _token_address not in token_info[chain_id]:
        raise HTTPException(status_code=404, detail=f"Token info for {token_address} on chain {chain_id} has never been initialized.")
    
    token_info[chain_id][_token_address][key] = value

    await post_token_last_updated(chain_id, _token_address)

    return response({key: token_info[chain_id][_token_address][key]})


@router.get("/info/{chain_id}/{token_address}")
async def get_token_info(chain_id: int, token_address: str):
    """
    Get the token information for a given token address on a given blockchain.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Returns:__
    - **OK**: Returns the token information as a JSON response if the call to fetch information from the cache was successful.

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
    
    return response(token_info[chain_id][_token_address])


@router.post("/info/socials/{chain_id}/{token_address}")
async def post_token_socials(chain_id: int, token_address: str):
    """
    Post the token social information for a given token address on a given blockchain retrieved from an external API.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Returns:__
    - **OK**: Returns the token information as a JSON response if the call to fetch information from the external API was successful.
    - **NOTOK**: Returns an error message as a JSON response if the call to fetch information from the external API failed.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    - **404 Not Found**: If the token address has never been updated.
    """

    if chain_id not in token_info:
        raise HTTPException(status_code=400, detail=f"Chain ID {chain_id} is not supported.")
    
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is not valid.")
    
    _token_address = token_address.lower()

    if _token_address not in token_info[chain_id]:
        await initialize_token_info(chain_id, _token_address)

    if token_info[chain_id][_token_address]['name'] is None:
        try:
            info = await fetch_token_socials(_token_address)

            if info.status == 1:
                for key in info.result.keys():
                    token_info[chain_id][_token_address][key] = info.result[key]
            else:
                return error(f"Token info for {_token_address} on chain {chain_id} could not be fetched. {info.result}")

            await post_token_last_updated(chain_id, _token_address)

            return response(token_info[chain_id][_token_address])
        except Exception as e:
            return error(f"An exception occurred with error: {e}.")

    return response(token_info[chain_id][_token_address])


@router.post("/info/price/{chain_id}/{token_address}")
async def post_token_price(chain_id: int, token_address: str):
    """
    Post the latest price for a given token address on a given blockchain.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Returns:__
    - **OK**: Returns the latest price as a JSON response if the call to fetch information from the cache was successful.

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
        price = float(random.randint(0, 10000) / 10000)
        await patch_token_info(chain_id, _token_address, 'price', price)
    elif token_info[chain_id][_token_address]['price'] is None:
        price = float(random.randint(0, 10000) / 10000)
        await patch_token_info(chain_id, _token_address, 'price', price)

    return response({'price': token_info[chain_id][_token_address]['price']})


@router.post("/info/liquidity/{chain_id}/{token_address}")
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

    __Returns:__
    - **OK**: Returns the latest liquidity information as a JSON response if the call to fetch information from the cache was successful.

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

    if token_info[chain_id][_token_address]['deployer'] is None:
        try:
            url = 'https://api.gopluslabs.io/api/v1/token_security/1'

            params = {
                'contract_addresses': _token_address
            }

            request_response = requests.get(url, params=params)
            request_response.raise_for_status()
            
            if request_response.status_code == 200:
                data = request_response.json()

                token_info[chain_id][_token_address]['deployer'] = data['result'][_token_address]['creator_address']
                token_info[chain_id][_token_address]['holder_count'] = int(data['result'][_token_address]['holder_count'])
                token_info[chain_id][_token_address]['buy_tax'] = float(data['result'][_token_address]['buy_tax'])
                token_info[chain_id][_token_address]['sell_tax'] = float(data['result'][_token_address]['sell_tax'])

                dex_liquidity = data['result'][_token_address]['dex']

                token_info[chain_id][_token_address]['dex_liquidity_usd'] = sum([float(item['liquidity']) for item in dex_liquidity])
            else:
                return error("Failed to fetch token security information from GoPlus.")

            await post_token_last_updated(chain_id, _token_address)
        except Exception as e:
            return error(f"An exception occurred whilst attempting to fetch token security information from GoPlus: {e}")
    
    return response(token_info[chain_id][_token_address])


@router.post("/info/{chain_id}/{token_address}")
async def post_token_info(chain_id: int, token_address: str):
    """
    Post the latest information for a given token address on a given blockchain.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Returns:__
    - **OK**: Returns the latest information as a JSON response if the call to fetch information from the cache was successful.

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

    if token_info[chain_id][_token_address]['name'] is None:
        await post_token_socials(chain_id, _token_address)
    
    await post_token_liquidity_info(chain_id, _token_address)
    await post_token_price(chain_id, _token_address)

    return response(token_info[chain_id][_token_address])
