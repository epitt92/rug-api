from fastapi import HTTPException
from fastapi import APIRouter, HTTPException
import time
from core.models import ChartResponse, ChartData
import random, math, time, requests

router = APIRouter()

chain_name_mapping = {'ethereum': 1, 'bsc': 56, 'arbitrum': 42161}
chain_id_mapping = {k: v for v, k in chain_name_mapping.items()}

@router.get("/goplus/{chain}/{token_address}")
async def get_pool_address(chain_id: int, token_address: str):
    # Get the leading pool address from GoPlus API for a token and return it
    _token_address = token_address.lower()

    try:
        url = f'https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={_token_address}'

        request_response = requests.get(url)
        request_response.raise_for_status()

        data = request_response.json()
        if data.get('result').get(_token_address).get('dex'):
            dex = data.get('result').get(_token_address).get('dex')[0]
            return dex.get('pair')
        else:
            raise HTTPException(status_code=500, detail=f"Failed to get GoPlus data for token {token_address} on chain {chain_id}. The response did not contain DEX information.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get GoPlus data for token {token_address} on chain {chain_id}.")


@router.get("/{chain}/{token_address}", response_model=ChartResponse)
async def get_chart_data(chain: str, token_address: str, duration: str = '1d'):
    if chain not in chain_name_mapping:
        raise HTTPException(status_code=400, detail=f"Chain {chain} is invalid.")
    
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is invalid.")

    _token_address = token_address.lower()

    # Get the pool address from GoPlus API
    chain_id = chain_name_mapping[chain]
    pool_address = await get_pool_address(chain_id, _token_address)

    # Call CoinGecko API with pool address and correct frequency
    durations = {
        '1h': {'candleType': 'minute', 'candleDuration': 1},
        '4h': {'candleType': 'minute', 'candleDuration': 1},
        '1d': {'candleType': 'minute', 'candleDuration': 5},
        '1w': {'candleType': 'hour', 'candleDuration': 1},
        '1m': {'candleType': 'hour', 'candleDuration': 4},
        'all': {'candleType': 'hour', 'candleDuration': 12}
    }

    if duration not in durations:
        raise HTTPException(status_code=400, detail=f"Duration {duration} is invalid.")
    
    try:
        url = f"https://api.geckoterminal.com/api/v2/networks/eth/pools/{pool_address}/ohlcv/{durations[duration]['candleType']}"
        params = {
            "aggregate": durations[duration]['candleDuration'],
            "limit": 240
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            market_data = data['data']['attributes']['ohlcv_list']
    except:
        raise HTTPException(status_code=500, detail=f"Failed to get CoinGecko data for token {token_address} on chain {chain}.")

    # Refactor response to correct formatting
    N = len(market_data)
    output = []

    timestampArray = []
    priceArray = []

    # CoinGecko returns data in reverse chronological order
    for i in reversed(range(N)):
        row = market_data[i]
        timestamp, price, volume, marketCap = row[0], row[4], row[5], row[4]

        timestampArray.append(timestamp)
        priceArray.append(price)

        output.append(ChartData(timestamp=timestamp, price=price, volume=volume, marketCap=marketCap))

    timestampMin = min(timestampArray)
    timestampMax = max(timestampArray)
    priceMin = min(priceArray)
    priceMax = max(priceArray)

    # Modify priceMin and priceMax to add buffers
    l = (priceMax - priceMin) / 0.9
    priceMin -= l * 0.05
    priceMax += l * 0.05

    return ChartResponse(priceMin=priceMin, priceMax=priceMax, marketCapMin=priceMin, marketCapMax=priceMax, timestampMin=timestampMin, timestampMax=timestampMax, numDatapoints=N, data=output, latestPrice=priceArray[-1], latestReturn=(priceArray[-1] - priceArray[0]) / priceArray[0])
