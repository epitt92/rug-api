from fastapi import HTTPException, APIRouter
import requests, logging

from src.v1.shared.models import ChainEnum
from src.v1.shared.constants import CHAIN_ID_MAPPING
from src.v1.chart.constants import FREQUENCY_MAPPING
from src.v1.chart.models import FrequencyEnum
from src.v1.chart.schemas import ChartResponse, ChartData

logging.basicConfig(level=logging.INFO)

router = APIRouter()

async def get_pool_address(chain: ChainEnum, token_address: str):
    chain_id = CHAIN_ID_MAPPING.get(chain.value)

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
async def get_chart_data(chain: ChainEnum, token_address: str, frequency: FrequencyEnum):
    pool_address = await get_pool_address(chain, token_address)

    # Call CoinGecko API with pool address and correct frequency
    try:
        url = f"https://api.geckoterminal.com/api/v2/networks/eth/pools/{pool_address}/ohlcv/{FREQUENCY_MAPPING[frequency.value]['candleType']}"
        params = {
            "aggregate": FREQUENCY_MAPPING[frequency.value]['candleDuration'],
            "limit": 300
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            market_data = data['data']['attributes']['ohlcv_list']
    except:
        raise HTTPException(status_code=500, detail=f"Failed to get CoinGecko data for token {token_address} on chain {chain.value}.")

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
