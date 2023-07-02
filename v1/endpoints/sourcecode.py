from fastapi import HTTPException
from fastapi import APIRouter, HTTPException, Query
import time
from pydantic import Field
import time
from core.models import success, error, response
import os
import requests
import logging

router = APIRouter()

source_code = {1: {}}

@router.get("/check/{chain_id}/{token_address}")
async def check_source_code(chain_id: int, token_address: str):
    """
    Check whether the source code for a given token address on a given blockchain is available.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Returns:__
    - **OK**: Returns a success message indicating whether the source code is available.
    - **NOTOK**: Returns an error message indicating that the source code is not available.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    """
        
    if chain_id not in source_code:
        raise HTTPException(status_code=400, detail=f"Chain ID {chain_id} is not supported.")
    
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is invalid.")

    _token_address = token_address.lower()

    if _token_address not in source_code[chain_id]:
        return error('Source code not found.')
    else:
        return success('Source code found.')


async def fetch_source_code(token_address: str):
    api_key = os.getenv('ETHERSCAN_API_KEY')

    url = 'https://api.etherscan.io/api'

    params = {
        'module': 'contract',
        'action': 'getsourcecode',
        'address': token_address,
        'apikey': api_key
    }

    try:
        result = requests.get(url, params=params)
        result.raise_for_status()
        data = result.json()

        if data['status'] == "1":
            raw_data = data['result'][0]
            output = {'source_code': raw_data['SourceCode'], 'abi': raw_data['ABI']}
            return response(output)
        else:
            return error(f"An external API response error occurred with message: {data['message']}")
    except requests.exceptions.RequestException as e:
        return error(f"A request exception occurred with error: {e}.")


@router.post("/{chain_id}/{token_address}")
async def post_source_code(chain_id: int, token_address: str):
    """
    Post the source code for a given token address on a given blockchain to storage from an external API.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Returns:__
    - **OK**: Returns the source code of the token address on the given blockchain as a JSON.
    - **NOTOK**: Returns an error message indicating that the attempt to fetch the source code failed.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    """
        
    if chain_id not in source_code:
        raise HTTPException(status_code=400, detail=f"Chain ID {chain_id} is not supported.")
    
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is invalid.")

    _token_address = token_address.lower()

    if _token_address not in source_code[chain_id]:
        result = await fetch_source_code(_token_address)
        if result.status == 1:
            source_code[chain_id][_token_address] = result.result
            return response(source_code[chain_id][_token_address])
        else:
            return error('An error occurred while fetching source code.')
    else:
        return response(source_code[chain_id][_token_address])


@router.get("/{chain_id}/{token_address}")
async def get_source_code(chain_id: int, token_address: str):
    """
    Get the source code for a given token address on a given blockchain to storage from an external API.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Returns:__
    - **OK**: Returns the source code of the token address on the given blockchain as a JSON.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    - **404 Not Found**: If the token address does not have source code stored in memory.
    """
        
    if chain_id not in source_code:
        raise HTTPException(status_code=400, detail=f"Chain ID {chain_id} is not supported.")
    
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is invalid.")

    _token_address = token_address.lower()

    if _token_address not in source_code[chain_id]:
        raise HTTPException(status_code=404, detail=f"Token address {token_address} does not have source code stored in memory.")
    else:
        return response(source_code[chain_id][_token_address])
