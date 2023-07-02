from fastapi import HTTPException
from fastapi import APIRouter, HTTPException, Query
import time
from pydantic import Field
import time
from core.models import success, error, response
import os
import requests
import logging
import numpy as np
from dotenv import load_dotenv
import json

load_dotenv()

mapping = None
with open('v1/utils/labels.json') as f:
    mapping = json.load(f)

router = APIRouter()

minutes = 60
contract_info = {1: {}}
SECTIONS = ["Supply", "Transferability"]

@router.post("/{chain_id}/{token_address}")
async def post_token_contract_info(chain_id: int, token_address: str):
    """
    Fetches the contract information for a given token address on a given blockchain.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Returns:__
    - **OK**: Returns the token contract information as a JSON response if the call to fetch information from the cache was successful.

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

                information = {'timestamp': int(time.time())}
                for key, item in mapping.items():
                    if key in data_response:
                        information[key] = {**item, **{'value': data_response[key]}}

                contract_info[chain_id][_token_address] = information
            else:
                return error("Failed to fetch token security information from GoPlus.")
        except Exception as e:
            return error(f"An exception occurred whilst attempting to fetch token security information from GoPlus: {e}")

    return response(contract_info[chain_id][_token_address])


async def get_token_info_section(chain_id: int, token_address: str, section: str):
    """
    Fetches the contract information for a given token address on a given blockchain.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Returns:__
    - **OK**: Returns the token contract information as a JSON response if the call to fetch information from the cache was successful.

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
    
    if section not in SECTIONS:
        raise HTTPException(status_code=400, detail=f"Section {section} is not valid.")
    
    _token_address = token_address.lower()

    if _token_address not in contract_info[chain_id]:
        return error("Token address not found in cache.")
    
    information = contract_info[chain_id][_token_address]

    output = {}
    for key, item in information.items():
        if key == 'timestamp':
            continue
        if item.get('section') == section:
            output[key] = item

    return response(output)


@router.get("/supply/{chain_id}/{token_address}")
async def get_token_contract_supply_info(chain_id: int, token_address: str):
    """
    Fetches the token contract supply section information and labels for a given token address on a given blockchain.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Returns:__
    - **OK**: Returns the token contract supply section information and labels as a JSON response if the call to fetch information from the cache was successful.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    """
    return await get_token_info_section(chain_id, token_address, 'Supply')


@router.get("/transferability/{chain_id}/{token_address}")
async def get_token_contract_transferability_info(chain_id: int, token_address: str):
    """
    Fetches the token contract transferability section information and labels for a given token address on a given blockchain.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Returns:__
    - **OK**: Returns the token contract transferability section information and labels as a JSON response if the call to fetch information from the cache was successful.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    """
    return await get_token_info_section(chain_id, token_address, 'Transferability')
