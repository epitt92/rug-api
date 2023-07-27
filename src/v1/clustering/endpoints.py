from fastapi import APIRouter, HTTPException
import os
import requests

from src.v1.clustering.schemas import ClusterResponse

router = APIRouter()


# @router.get("/holders/{chain_id}/{token_address}")
async def fetch_holder_list(chain_id: int, token_address: str):
    api_key = os.getenv('ETHERSCAN_API_KEY')

    url = 'https://api.etherscan.io/api'

    # TODO: Should fetch the number of holders and then paginate this query accordingly

    params = {
        'module': 'token',
        'action': 'tokenholderlist',
        'contractaddress': token_address,
        'page': 1,
        'offset': 10000,
        'apikey': api_key
    }

    try:
        result = requests.get(url, params=params)
        result.raise_for_status()
        data = result.json()

        if data['status'] == "1":
            result = data.get('result')
            addresses, amounts = [item.get('TokenHolderAddress') for item in result], [float(item.get('TokenHolderQuantity')) for item in result]
            return dict(zip(addresses, amounts))
        else:
            raise HTTPException(status_code=500, detail=f"An unknown error occurred during the call to fetch token holders for token {token_address} on chain {chain_id}.")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"An unknown error occurred during the call to fetch token holders for token {token_address} on chain {chain_id}.")


async def fetch_transfers(sender_address: str):
    url = 'https://api.etherscan.io/api'

    # Get transfer data for a given sender address
    params = {
        'module': 'account',
        'action': 'txlist',
        'address': sender_address,
        'sort': 'desc',
        'startblock': 12493516,
        'apikey': os.getenv('ETHERSCAN_API_KEY')
    }

    result = requests.get(url, params=params)
    result.raise_for_status()
    data = result.json().get('result')

    transfers = [item for item in data if item['functionName'] == '']
    return transfers


@router.get("/liquidity/{chain}/{token_address}", response_model=ClusterResponse)
async def get_cluster(chain_id: int, token_address: str):

    return ClusterResponse()
