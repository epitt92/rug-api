from fastapi import HTTPException, APIRouter
import requests, logging

from src.v1.shared.models import ChainEnum
from src.v1.shared.constants import CHAIN_ID_MAPPING
from src.v1.chart.constants import FREQUENCY_MAPPING
from src.v1.chart.dependencies import process_market_data
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
        raise HTTPException(status_code=500, detail=f"Failed to get GoPlus data for token {token_address} on chain {chain_id}. Exception: {e}")


@router.get("/{chain}/{token_address}", response_model=ChartResponse)
async def get_chart_data(chain: ChainEnum, token_address: str, frequency: FrequencyEnum):
    logging.info(f'Fetching chart data for {token_address} on chain {chain}, via chart...')

    pool_address = await get_pool_address(chain, token_address)

    # Call CoinGecko API with pool address and correct frequency
    try:
        if chain == ChainEnum.ethereum:
            network = 'eth'
        elif chain == ChainEnum.arbitrum:
            network = 'arbitrum'
        elif chain == ChainEnum.base:
            network = 'base'
        else:
            raise HTTPException(status_code=500, detail=f"Failed to get CoinGecko data for token {token_address} on chain {chain}. The chain {chain} is not supported.")
        
        url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/{FREQUENCY_MAPPING[frequency.value]['candleType']}"

        params = {
            "aggregate": FREQUENCY_MAPPING[frequency.value]['candleDuration'],
            "limit": FREQUENCY_MAPPING[frequency.value]['limit']
        }

        response = requests.get(url, params=params)

        logging.info(f"CoinGecko API response status code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            logging.info(f"CoinGecko API response data: {data}")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to get CoinGecko data for token {token_address} on chain {chain}. The response status code was {response.status_code}.")
    except:
        raise HTTPException(status_code=500, detail=f"Failed to get CoinGecko data for token {token_address} on chain {chain}.")

    market_data = data['data']['attributes'].get('ohlcv_list')

    if not market_data:
        raise HTTPException(status_code=500, detail=f"Failed to get CoinGecko data for token {token_address} on chain {chain}: No data was returned.")

    return process_market_data(market_data)


@router.get("/{chain}/pool/{pool_address}", response_model=ChartResponse)
async def get_chart_data_from_pool(chain: ChainEnum, pool_address: str, frequency: FrequencyEnum):
    logging.info(f'Fetching chart data for pool {pool_address} on chain {chain}, via chart...')

    # Call CoinGecko API with pool address and correct frequency
    try:
        logging.info(f'Chain: {chain}')
        logging.info(f'ChainEnum: {ChainEnum.ethereum}')

        if chain == ChainEnum.ethereum:
            network = 'eth'
        elif chain == ChainEnum.arbitrum:
            network = 'arbitrum'
        elif chain == ChainEnum.base:
            network = 'base'
        else:
            raise HTTPException(status_code=500, detail=f"Failed to get CoinGecko data for pool {pool_address} on chain {chain}. The chain {chain} is not supported.")
        
        url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/{FREQUENCY_MAPPING[frequency.value]['candleType']}"

        logging.info(f'Attempting to fetch data via URL: {url}')
        params = {
            "aggregate": FREQUENCY_MAPPING[frequency.value]['candleDuration'],
            "limit": FREQUENCY_MAPPING[frequency.value]['limit']
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
        else:
            raise HTTPException(status_code=500, detail=f"Failed to get CoinGecko data for pool {pool_address} on chain {chain}. The response status code was {response.status_code}.")
    except:
        raise HTTPException(status_code=500, detail=f"Failed to get CoinGecko data for pool {pool_address} on chain {chain}.")

    market_data = data['data']['attributes'].get('ohlcv_list')

    if not market_data:
        raise HTTPException(status_code=500, detail=f"Failed to get CoinGecko data for pool {pool_address} on chain {chain}: No data was returned.")

    return process_market_data(market_data)
