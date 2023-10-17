from fastapi import HTTPException, APIRouter, Depends
import requests, logging

from src.v1.shared.models import ChainEnum, validate_token_address
from src.v1.shared.exceptions import UnsupportedChainException, GoPlusDataException

from src.v1.shared.constants import CHAIN_ID_MAPPING
from src.v1.chart.constants import FREQUENCY_MAPPING
from src.v1.chart.dependencies import process_market_data
from src.v1.chart.models import FrequencyEnum
from src.v1.chart.schemas import ChartResponse
from src.v1.chart.exceptions import CoinGeckoChartException

from src.v1.auth.endpoints import decode_token

logging.basicConfig(level=logging.INFO)

router = APIRouter()

async def get_pool_address(chain: ChainEnum, token_address: str = Depends(validate_token_address)):
    chain_id = CHAIN_ID_MAPPING.get(chain.value)

    if not chain_id:
        logging.error(f"Exception: Fetching the Chain ID for the chain {chain.value}.")
        raise UnsupportedChainException(chain=chain.value)

    # Get the leading pool address from GoPlus API for a token and return it
    try:
        url = f'https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={token_address}'

        request_response = requests.get(url)
        request_response.raise_for_status()
    except Exception as e:
        logging.error(f"Exception: Whilst calling GoPlus Labs for the response for token {token_address} on chain {chain}: {e}")
        raise GoPlusDataException(chain=chain, token_address=token_address)

    data = request_response.json()

    try:
        pair_address = data.get('result').get(token_address).get('dex')
    except KeyError as e:
        logging.error(f"Exception: KeyError in `data` from the GoPlus response: {data}. Exception: {e}")
        raise GoPlusDataException(chain=chain, token_address=token_address)
    except Exception as e:
        logging.error(f"Exception: An uncaught Exception whilst attempting to extract the pair address from the GoPlus response: {e}")
        raise GoPlusDataException(chain=chain, token_address=token_address)

    if pair_address:
        return pair_address[0].get('pair')
    else:
        logging.error(f"Exception: `pair_address` was not defined for the GoPlus response from {token_address} on chain {chain}.")
        raise GoPlusDataException(chain=chain, token_address=token_address)

@router.get("/{chain}/{token_address}", dependencies=[Depends(decode_token)], response_model=ChartResponse)
async def get_chart_data(chain: ChainEnum, frequency: FrequencyEnum, token_address: str = Depends(validate_token_address)):
    # TODO: Eventually want to store pool address as part of the metadata, and do a call to fetch it from there
    pool_address = await get_pool_address(chain, token_address)

    try:
        frequency_value = FREQUENCY_MAPPING.get(frequency.value).get('candleType')
        frequency_aggregate = FREQUENCY_MAPPING.get(frequency.value).get('candleDuration')
        frequency_limit = FREQUENCY_MAPPING.get(frequency.value).get('limit')
    except Exception as e:
        logging.error(f"Exception: The frequency {frequency} provided is not supported. {e}")
        raise CoinGeckoChartException(chain=chain, token_address=token_address, frequency=frequency)

    if chain == ChainEnum.ethereum:
        network = 'eth'
    elif chain == ChainEnum.arbitrum:
        network = 'arbitrum'
    elif chain == ChainEnum.base:
        network = 'base'
    else:
        raise UnsupportedChainException(chain=chain)

    # Call CoinGecko API with pool address and correct frequency
    try:
        url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/{frequency_value}"

        params = {
            "aggregate": frequency_aggregate,
            "limit": frequency_limit
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Exception: Whilst calling the CoinGecko API: {e}")
        raise CoinGeckoChartException(token_address=token_address, chain=chain, frequency=frequency)

    if response.status_code == 200:
        data = response.json()
    else:
        logging.error(f"Exception: The response status code from CoinGecko was {response.status_code}.")
        raise CoinGeckoChartException(chain=chain, token_address=token_address, frequency=frequency)

    try:
        market_data = data['data']['attributes'].get('ohlcv_list')
    except KeyError as e:
        logging.error(f"Exception: KeyError on `market_data` object when attempting to fetch OHLCV list. {e}")
        raise CoinGeckoChartException(chain=chain, token_address=token_address, frequency=frequency)

    if not market_data:
        logging.error(f"Exception: The response did not contain any market data.")
        raise CoinGeckoChartException(chain=chain, token_address=token_address, frequency=frequency)

    try:
        return process_market_data(market_data)
    except Exception as e:
        logging.error("Exception: {e}")
        raise CoinGeckoChartException(chain=chain, token_address=token_address, frequency=frequency)


# @router.get("/{chain}/pool/{pool_address}", response_model=ChartResponse)
# async def get_chart_data_from_pool(chain: ChainEnum, frequency: FrequencyEnum, pool_address: str = Depends(validate_token_address)):
#     # Call CoinGecko API with pool address and correct frequency
#     try:
#         if chain == ChainEnum.ethereum:
#             network = 'eth'
#         elif chain == ChainEnum.arbitrum:
#             network = 'arbitrum'
#         elif chain == ChainEnum.base:
#             network = 'base'
#         else:
#             raise HTTPException(status_code=500, detail=f"Failed to get CoinGecko data for pool {pool_address} on chain {chain}. The chain {chain} is not supported.")
        
#         url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/{FREQUENCY_MAPPING[frequency.value]['candleType']}"

#         params = {
#             "aggregate": FREQUENCY_MAPPING[frequency.value]['candleDuration'],
#             "limit": FREQUENCY_MAPPING[frequency.value]['limit']
#         }

#         response = requests.get(url, params=params)

#         if response.status_code == 200:
#             data = response.json()
#         else:
#             raise HTTPException(status_code=500, detail=f"Failed to get CoinGecko data for pool {pool_address} on chain {chain}. The response status code was {response.status_code}.")
#     except:
#         raise HTTPException(status_code=500, detail=f"Failed to get CoinGecko data for pool {pool_address} on chain {chain}.")

#     market_data = data['data']['attributes'].get('ohlcv_list')

#     if not market_data:
#         raise HTTPException(status_code=500, detail=f"Failed to get CoinGecko data for pool {pool_address} on chain {chain}: No data was returned.")

#     return process_market_data(market_data)
