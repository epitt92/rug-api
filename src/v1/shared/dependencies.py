import random, logging
from typing import Union
from web3 import Web3
import json, dotenv, os, time
from goplus import auth

from src.v1.shared.constants import *
from src.v1.shared.models import ChainEnum
from src.v1.shared.schemas import Chain
from src.v1.shared.exceptions import RPCProviderException, UnsupportedChainException, GoPlusAccessKeyLoadError, GoPlusAccessKeyRefreshError

dotenv.load_dotenv()

with open('src/v1/shared/files/erc20.json', 'r') as f:
    ERC20_ABI = json.load(f) 

# Set-up RPC providers for each chain
ETHEREUM_RPC = Web3(Web3.HTTPProvider(os.getenv('ETHEREUM_RPC_URL')))
ARBITRUM_RPC = Web3(Web3.HTTPProvider(os.getenv('ARBITRUM_RPC_URL')))
BASE_RPC = Web3(Web3.HTTPProvider(os.getenv('BASE_RPC_URL')))

def get_chain(chain: ChainEnum):
    _chain = str(chain.value) if isinstance(chain, ChainEnum) else str(chain)

    if _chain == 'ethereum':
        return Chain(chainId=ETHEREUM_CHAIN_ID)
    elif _chain == 'arbitrum':
        return Chain(chainId=ARBITRUM_CHAIN_ID)
    elif _chain == 'base':
        return Chain(chainId=BASE_CHAIN_ID)
    else:
        raise ValueError(f"Invalid Chain on call to `get_chain`: {_chain}")
    

def get_rpc_provider(chain: ChainEnum):
    _chain = str(chain.value) if isinstance(chain, ChainEnum) else str(chain)

    if _chain == 'ethereum':
        return ETHEREUM_RPC
    elif _chain == 'arbitrum':
        return ARBITRUM_RPC
    elif _chain == 'base':
        return BASE_RPC
    else:
        raise UnsupportedChainException(f"Invalid Chain on call to `get_chain`: {_chain}")


def get_primary_key(token_address: str, chain: Union[str, ChainEnum]) -> str:
    if isinstance(chain, ChainEnum):
        return f"{token_address.lower()}_{str(chain.value)}"
    else:
        return f"{token_address.lower()}_{str(chain)}"


async def get_token_contract_details(chain: ChainEnum, token_address: str) -> dict:
    RPC = get_rpc_provider(chain)

    try:
        _token_address = RPC.to_checksum_address(token_address)
        contract = RPC.eth.contract(_token_address, abi=ERC20_ABI)
    except Exception as e:
        logging.warning(f'An exception occurred whilst trying to create an ERC20 object for token {token_address} on chain {chain}: {e}')
        raise RPCProviderException()
    
    try:
        token_name = str(contract.functions.name().call())
        token_symbol = str(contract.functions.symbol().call())
        return {'name': token_name, 'symbol': token_symbol}
    except Exception as e:
        logging.warning(f'An exception occurred whilst trying to fetch token details for token {token_address} on chain {chain}: {e}')
        raise e

def fetch_access_token():
    # Log the start time of the request
    current_time = int(time.time())
    
    try:
        token_data = auth.Auth(key=os.getenv('GO_PLUS_APP_KEY'), secret=os.getenv('GO_PLUS_APP_SECRET')).get_access_token()
    except Exception as e:
        logging.error(f"Exception: An exception occurred whilst attempting to fetch a new access token from GoPlus.")
        raise GoPlusAccessKeyRefreshError()
        
    try:
        access_token = token_data.result.access_token
        expires_in = token_data.result.expires_in
        data = {"access_token": access_token, "expiry": current_time + expires_in - 120}
    except Exception as e:
        logging.warning(f"Exception: An exception occurred whilst attempting to parse the access token response from GoPlus.")
        raise GoPlusAccessKeyRefreshError()
    
    try:
        with open("src/v1/shared/files/access_token.json", "w") as f:
            json.dump(data, f)
    except FileNotFoundError:
        logging.warning(f"Exception: The access token file could not be found whilst trying to save a new access token from GoPlus.")
        raise GoPlusAccessKeyRefreshError()
    except Exception as e:
        logging.warning(f"Exception: An exception occurred whilst attempting to save a new access token from GoPlus.")
        raise GoPlusAccessKeyRefreshError()

def load_access_token():
    try:
        with open("src/v1/shared/files/access_token.json", "r") as f:
            access_token = json.load(f)
    except FileNotFoundError:
        try:
            fetch_access_token()
            return load_access_token()
        except Exception as e:
            logging.error(f"Exception: An exception occurred whilst attempting to fetch a new access token from GoPlus.")
            raise GoPlusAccessKeyLoadError()
        
    if (access_token.get("expiry") < int(time.time())):
        try:
            logging.info(f"Access token expired, fetching a new one...")
            fetch_access_token()
            logging.info(f"Access token fetched, loading it...")
            return load_access_token()
        except Exception as e:
            logging.error(f"Exception: An exception occurred whilst attempting to fetch a new access token from GoPlus.")
            raise GoPlusAccessKeyLoadError()
    else:
        return access_token.get("access_token")
