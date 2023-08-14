from fastapi import APIRouter
import requests, json, time, dotenv, logging, os

from src.v1.shared.DAO import DAO
from src.v1.shared.dependencies import get_primary_key
from src.v1.sourcecode.models import ChainEnum
from src.v1.sourcecode.schemas import SourceCodeResponse, SourceCodeFile

router = APIRouter()

dotenv.load_dotenv()

SOURCE_CODE_DAO = DAO('sourcecode')

async def fetch_raw_code(chain: ChainEnum, token_address: str) -> str:
    logging.info(f'Chain: {chain}')

    _chain = str(chain.value) if isinstance(chain, ChainEnum) else str(chain)

    logging.info(f'Chain: {_chain}')

    if _chain == 'ethereum':
        response = requests.get(f"{os.environ.get('ETHEREUM_BLOCK_EXPLORER_URL')}?module=contract&action=getsourcecode&address={token_address}&apikey={os.environ.get('ETHEREUM_BLOCK_EXPLORER_API_KEY')}")
        data = response.json().get('result')[0]

        logging.info(f'Data: {data}')
        
        source = data.get('SourceCode')
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
            logging.info(f'An error occurred: {e}')
    else:
        return source
    

@router.get("/{chain}/{token_address}/map", include_in_schema=True)
async def get_source_code_map(chain: ChainEnum, token_address: str):
    source = await parse_raw_code(await fetch_raw_code(chain, token_address))
    if isinstance(source, str):
        if len(source) == 0:
            return {'Flattened Source Code': 'No source code available for this contract.'}
        return {'Flattened Source Code': source}
    elif isinstance(source, dict):
        # Pre-process dictionary keys and return
        new_keys = [file.split('/')[-1] for file in source.keys() if file.endswith('.sol')]
        key_map = dict(zip(source.keys(), new_keys))
        return {key_map.get(key): source.get(key).get('content') for key in source.keys()}


@router.get("/{chain}/{token_address}", response_model=SourceCodeResponse)
async def get_source_code(chain: ChainEnum, token_address: str):
    _token_address = token_address.lower()

    # Check if the token source code has already been cached
    pk = get_primary_key(_token_address, chain.value)

    # Attempt to fetch transfers from DAO object
    _source_code_map = SOURCE_CODE_DAO.find_most_recent_by_pk(pk)

    # If source code is found, return it
    if not _source_code_map:
        _source_code_map = await get_source_code_map(chain.value, _token_address)

        # Write source code map to DAO file
        SOURCE_CODE_DAO.insert_one(partition_key_value=pk, item={'timestamp': int(time.time()), 'sourcecode': _source_code_map})
    else:
        _source_code_map = _source_code_map.get('sourcecode')

    output = []
    for key, value in _source_code_map.items():
        output.append(SourceCodeFile(name=key, sourceCode=value))

    return SourceCodeResponse(files=output)
