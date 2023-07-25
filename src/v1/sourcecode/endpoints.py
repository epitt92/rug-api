from fastapi import HTTPException, APIRouter, HTTPException
import os, requests, json

from src.v1.sourcecode.models import ChainEnum
from src.v1.sourcecode.schemas import SourceCodeResponse, SourceCodeFile

router = APIRouter()

async def fetch_raw_code(token_address: str = '0x163f8C2467924be0ae7B5347228CABF260318753') -> str:
    response = requests.get(f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={token_address}&apikey=GV1BQXWFT1FKAKUJTJ1E1QPGYMNDWBQXB6")
    data = response.json().get('result')[0]
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
            print(f'An error occurred: {e}')
    else:
        return source
    
async def get_source_code_map(token_address: str = '0x163f8C2467924be0ae7B5347228CABF260318753'):
    source = await parse_raw_code(await fetch_raw_code(token_address))
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
    """
    Get the source code for a given token address on a given blockchain to storage from an external API.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Returns:__
    - **OK**: Returns the source code of the token address on the given blockchain as a JSON.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    - **404 Not Found**: If the token address does not have source code stored in memory.
    """
        
    source_code_map = await get_source_code_map(token_address)
    output = []
    for key, value in source_code_map.items():
        output.append(SourceCodeFile(name=key, sourceCode=value))

    return SourceCodeResponse(files=output)
