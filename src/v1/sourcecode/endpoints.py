from fastapi import APIRouter, HTTPException, Depends
import requests, json, time, dotenv, logging, os
from botocore.exceptions import ClientError

from src.v1.shared.DAO import DAO
from src.v1.shared.dependencies import get_primary_key
from src.v1.shared.models import validate_token_address
from src.v1.sourcecode.schemas import SourceCodeResponse, SourceCodeFile

from src.v1.shared.models import ChainEnum
from src.v1.shared.exceptions import DatabaseLoadFailureException, DatabaseInsertFailureException, UnsupportedChainException

router = APIRouter()

dotenv.load_dotenv()

######################################################
#                                                    #
#                Database Adapters                   #
#                                                    #
######################################################

SOURCE_CODE_DAO = DAO('sourcecode')

######################################################
#                                                    #
#                     Endpoints                      #
#                                                    #
######################################################

async def fetch_raw_code(chain: ChainEnum, token_address: str = Depends(validate_token_address)) -> str:
    _chain = str(chain.value) if isinstance(chain, ChainEnum) else str(chain)

    prefix = os.environ.get(f'{_chain.upper()}_BLOCK_EXPLORER_URL')
    api_key = os.environ.get(f'{_chain.upper()}_BLOCK_EXPLORER_API_KEY')
    
    payload = {
        'module': 'contract',
        'action': 'getsourcecode',
        'address': token_address,
        'apikey': api_key
    }

    response = requests.get(prefix, params=payload)
    data = response.json()

    logging.info(f'Fetched raw source code for {token_address} on chain {chain}')
    data = response.json().get('result')[0]
    
    source = data.get('SourceCode')

    logging.info(f'Fetched source code for {token_address} on chain {chain}')

    return source


async def parse_raw_code(source: str) -> dict:
    if source.startswith('{'):
        # Clean up the source by removing the extra curly braces and newline characters
        clean_source = source.replace('{{', '{').replace('}}', '}').replace('\r', '').replace('\n', '')

        # Parse the clean_source string into a dictionary
        try:
            parsed_source = json.loads(clean_source)
            return parsed_source.get('sources')
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse source code file. Error: {e}")
    else:
        return source


async def get_source_code_map(chain: ChainEnum, token_address: str = Depends(validate_token_address)):
    logging.info(f'Fetching source code map for {token_address} on chain {chain}, via map...')
    source = await parse_raw_code(await fetch_raw_code(chain, token_address))
    logging.info(f'Raw souce code: {source}')

    if isinstance(source, str):
        if len(source) == 0:
            return {'Flattened Source Code': 'No source code available for this contract.'}
        return {'Flattened Source Code': source}
    elif isinstance(source, dict):
        # Pre-process dictionary keys and return
        new_keys = [file.split('/')[-1] for file in source.keys() if file.endswith('.sol')]

        if len(new_keys) == 0 and len(source.keys()) == 1:
            return {'Flattened Source Code': source.get(list(source.keys())[0]).get('content')}
        elif len(new_keys) == 0:
            raise HTTPException(status_code=500, detail=f"Failed to fetch raw source code file, or no source code available for this contract.")

        key_map = dict(zip(source.keys(), new_keys))
        return {key_map.get(key): source.get(key).get('content') for key in source.keys()}


@router.get("/{chain}/{token_address}", response_model=SourceCodeResponse)
async def get_source_code(chain: ChainEnum, token_address: str = Depends(validate_token_address)):
    # Check if the token source code has already been cached
    pk = get_primary_key(token_address, chain.value)

    _chain = str(chain.value) if isinstance(chain, ChainEnum) else str(chain)

    if _chain != 'ethereum':
        logging.error(f'Exception: The chain {chain} is not supported by the `get_source_code` endpoint.')
        raise UnsupportedChainException(chain=chain)

    logging.debug(f'Fetching source code for {token_address} on chain {chain} from the database...')

    # Attempt to fetch transfers from DAO object
    _source_code_map = SOURCE_CODE_DAO.find_most_recent_by_pk(pk)
    
    # If source code is found, return it
    if not _source_code_map:
        logging.info(f'No source code found for {token_address} on chain {chain}. Fetching from API...')
        _source_code_map = await get_source_code_map(chain.value, token_address)

        # Write source code map to DAO file
        if _source_code_map is not None:
            try:
                logging.info(f'Writing source code map for {token_address} on chain {chain} to DAO...')
                SOURCE_CODE_DAO.insert_one(partition_key_value=pk, item={'timestamp': int(time.time()), 'sourcecode': _source_code_map})
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    logging.warning(f'Source code map for {token_address} on chain {chain} already exists in DAO.')
                    logging.warning(f'We do not allow duplicate writes for source code, since it is immutable.')
                    raise e
                else:
                    logging.warning(f'An unknown boto3 exception occurred while writing source code map for {token_address} on chain {chain} to DAO: {e}')
                    raise e
            except Exception as e:
                logging.warning(f'An unknown exception occurred while writing source code map for {token_address} on chain {chain} to DAO: {e}')
                raise e
        else:
            raise HTTPException(status_code=404, detail=f'No source code found for {token_address} on chain {chain.value}')
    else:
        logging.info(f'Found source code for {token_address} on chain {chain} in DAO.')
        _source_code_map = _source_code_map.get('sourcecode')

    output = []
    for key, value in _source_code_map.items():
        output.append(SourceCodeFile(name=key, sourceCode=value))

    return SourceCodeResponse(files=output)
