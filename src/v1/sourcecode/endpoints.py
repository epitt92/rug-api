from fastapi import APIRouter, HTTPException, Depends
import requests, json, time, dotenv, logging, os
from botocore.exceptions import ClientError
from pydantic import ValidationError

from src.v1.shared.DAO import DAO
from src.v1.shared.dependencies import get_primary_key
from src.v1.shared.models import validate_token_address
from src.v1.sourcecode.schemas import SourceCodeResponse, SourceCodeFile

from src.v1.shared.models import ChainEnum
from src.v1.shared.exceptions import DatabaseLoadFailureException, DatabaseInsertFailureException, UnsupportedChainException, BlockExplorerDataException, OutputValidationError

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

    if not prefix:
        logging.error(f"The environment variable '{_chain.upper()}_BLOCK_EXPLORER_URL' was not found.")
        raise Exception(f"The environment variable '{_chain.upper()}_BLOCK_EXPLORER_URL' was not found.")

    if not api_key:
        logging.error(f"The environment variable '{_chain.upper()}_BLOCK_EXPLORER_API_KEY' was not found.")
        raise Exception(f"The environment variable '{_chain.upper()}_BLOCK_EXPLORER_API_KEY' was not found.")

    payload = {
        'module': 'contract',
        'action': 'getsourcecode',
        'address': token_address,
        'apikey': api_key
    }

    try:
        response = requests.get(prefix, params=payload)
        data = response.json()
    except Exception as e:
        logging.error(f"Exception: During the call to GET getsourcecode from the Block Explorer for token {token_address} on chain {chain}: {e}")
        raise BlockExplorerDataException(chain=chain, token_address=token_address)

    logging.debug(f'Fetched raw source code for {token_address} on chain {chain}.')

    try:
        data = data.get('result')[0]
        source = data.get('SourceCode')
    except Exception as e:
        logging.error(f"Exception: An error occurred whilst attempting to handle the `data` object: {data}. Exception: {e}")
        return None

    logging.debug(f'Fetched source code for {token_address} on chain {chain}.')
    return source


async def parse_raw_code(source: str) -> dict:
    if not source:
        return None
    
    if source.startswith('{'):
        # Clean up the source by removing the extra curly braces and newline characters
        clean_source = source.replace('{{', '{').replace('}}', '}').replace('\r', '').replace('\n', '')

        # Parse the clean_source string into a dictionary

        # TODO: Raise suitable exception here
        try:
            parsed_source = json.loads(clean_source)
            return parsed_source.get('sources')
        except Exception as e:
            logging.error(f"Exception: While loading `clean_source` into a JSON object: {clean_source}. Exception: {e}")
            raise Exception(f"Exception: While loading `clean_source` into a JSON object: {clean_source}. Exception: {e}")
    else:
        return source


async def get_source_code_map(chain: ChainEnum, token_address: str = Depends(validate_token_address)):
    logging.debug(f'Fetching source code map for {token_address} on chain {chain}, via map...')

    try:
        source = await parse_raw_code(await fetch_raw_code(chain, token_address))
    except Exception as e:
        logging.error(f"Exception: During nested call to fetch and parse source code for {token_address} on chain {chain}: {e}")
        raise Exception(f"Exception: During nested call to fetch and parse source code for {token_address} on chain {chain}: {e}")

    if not source:
        return None
    
    if isinstance(source, str):
        if len(source) == 0:
            logging.debug(f"No source code was found. Returning an empty response.")
            return {'Flattened Source Code': 'No source code available for this contract.'}
        return {'Flattened Source Code': source}
    elif isinstance(source, dict):
        # Pre-process dictionary keys and return
        new_keys = [file.split('/')[-1] for file in source.keys() if file.endswith('.sol')]

        if len(new_keys) == 0 and len(source.keys()) == 1:
            return {'Flattened Source Code': source.get(list(source.keys())[0]).get('content')}
        elif len(new_keys) == 0:
            logging.error(f"Exception: The new keys list was empty for token {token_address} on chain {chain}.")
            raise Exception(f"Failed to fetch raw source code file, or no source code available for this contract.")

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
    try:
        _source_code_map = SOURCE_CODE_DAO.find_most_recent_by_pk(pk)
    except ClientError as e:
        logging.error(f"Exception: Boto3 exception whilst fetching data from 'sourcecode' with PK: {pk}")
        raise DatabaseLoadFailureException()
    except Exception as e:
        logging.error(f"Exception: Unknown exception whilst fetching data from 'sourcecode' with PK: {pk}")
        logging.error(f"Exception: {e}")
        raise DatabaseLoadFailureException()

    # If source code is found, return it
    if not _source_code_map:
        logging.debug(f'No source code found for {token_address} on chain {chain}. Fetching from API...')
        _source_code_map = await get_source_code_map(chain.value, token_address)

        # Write source code map to DAO file
        if _source_code_map is not None:
            try:
                logging.info(f'Writing source code map for {token_address} on chain {chain} to DAO...')
                SOURCE_CODE_DAO.insert_one(partition_key_value=pk, item={'timestamp': int(time.time()), 'sourcecode': _source_code_map})
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    logging.error(f'Exception: Source code map for {token_address} on chain {chain} already exists in DAO.')
                    logging.error(f'Exception: We do not allow duplicate writes for source code, since it is immutable.')
                else:
                    logging.error(f'Exception: An unknown boto3 exception occurred while writing source code map for {token_address} on chain {chain} to DAO: {e}')

                raise DatabaseInsertFailureException()
            except Exception as e:
                logging.warning(f'Exception: An unknown exception occurred while writing source code map for {token_address} on chain {chain} to DAO: {e}')
                raise DatabaseInsertFailureException()
        else:
            raise Exception(f'No source code found for {token_address} on chain {chain.value}')
    else:
        logging.debug(f'Found source code for {token_address} on chain {chain} in DAO.')
        _source_code_map = _source_code_map.get('sourcecode')

    output = []
    try:
        for key, value in _source_code_map.items():
            output.append(SourceCodeFile(name=key, sourceCode=value))
    except ValidationError as e:
        logging.error(f"Exception: A ValidationError was raised for SourceCodeFile: {e.json()}")
        raise OutputValidationError()
    except Exception as e:
        logging.error(f"Exception: An uncaught exception occurred was raised for SourceCodeFile: {e}")
        raise OutputValidationError()

    try:
        return SourceCodeResponse(files=output)
    except ValidationError as e:
        logging.error(f"Exception: A ValidationError was raised for SourceCodeResponse: {e.json()}")
        raise OutputValidationError()
    except Exception as e:
        logging.error(f"Exception: An uncaught exception occurred was raised for SourceCodeResponse: {e}")
        raise OutputValidationError()
