from fastapi import APIRouter, HTTPException
import time, os, requests, json
from dotenv import load_dotenv
from collections import defaultdict

from src.v1.shared.dependencies import get_random_score
from src.v1.shared.constants import CHAIN_ID_MAPPING
from src.v1.shared.models import ChainEnum
from src.v1.shared.exceptions import validate_token_address
from src.v1.tokens.schemas import TokenInfoResponse, TokenReviewResponse, TokenMetadata, ContractResponse, ContractItem, AISummary, AIComment, ClusterResponse, Holder
from src.v1.tokens.models import TokenMetadataEnum

load_dotenv()

mapping = None
with open('src/v1/tokens/files/labels.json') as f:
    mapping = json.load(f)

tokens = None
with open('src/v1/shared/files/tokens.json') as f:
    tokens = json.load(f)["tokens"]

router = APIRouter()

token_metadata = defaultdict(dict)
contract_info = defaultdict(dict)
score_mapping = defaultdict(dict)
review_mapping = defaultdict(dict)

async def patch_token_metadata(chain: ChainEnum, token_address: str, updateKey: TokenMetadataEnum, updateValue):    
    _token_address = token_address.lower()

    if _token_address not in token_metadata[chain.value]:
        raise HTTPException(status_code=404, detail=f"Token info for {token_address} on chain {chain.value} has never been initialized.")
    
    token_info_dict = token_metadata[chain.value][_token_address].dict()
    token_info_dict.update(**{updateKey: updateValue})
    token_metadata[chain.value][_token_address] = TokenMetadata(**token_info_dict)

    return token_metadata[chain.value][_token_address]


@router.get("/info/updated/{chain}/{token_address}")
async def get_token_last_updated(chain: ChainEnum, token_address: str):
    """
    Retrieve the UNIX timestamp at which a token was last updated.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Returns:__
    - **OK**: Returns the last updated UNIX timestamp as a JSON response.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    - **404 Not Found**: If the token address has never been updated.
    """
    validate_token_address(token_address)
    _token_address = token_address.lower()

    if _token_address not in token_metadata[chain.value]:
        raise HTTPException(status_code=404, detail=f"Token {_token_address} on chain {chain.value} has never been initialized.")
    
    return token_metadata[chain.value][_token_address].lastUpdatedTimestamp


async def initialize_token_metadata(chain: ChainEnum, token_address: str):
    validate_token_address(token_address)
    _token_address = token_address.lower()

    if _token_address not in token_metadata[chain.value]:
        # TODO: This will likely revert due to a lack of values for Token field, add method to fetch and cache required entries
        token_metadata[chain.value][_token_address] = TokenMetadata(tokenAddress=_token_address)
    
    return token_metadata[chain.value][_token_address]


async def get_block_explorer_data(token_address: str):
    api_key = os.getenv('ETHERSCAN_API_KEY')

    url = 'https://api.etherscan.io/api'

    params = {
        'module': 'token',
        'action': 'tokeninfo',
        'contractaddress': token_address,
        'apikey': api_key
    }

    try:
        result = requests.get(url, params=params)
        result.raise_for_status()
        data = result.json()

        if data['status'] == "1":
            raw_data = data['result'][0]

            output = {}
            output['name'] = raw_data['tokenName']
            output['symbol'] = raw_data['symbol']
            output['decimals'] = int(raw_data['divisor'])
            output['totalSupply'] = int(raw_data['totalSupply']) / (10 ** int(raw_data['divisor']))
            output['website'] = raw_data['website'] if raw_data['website'] != '' else None
            output['twitter'] = raw_data['twitter'] if raw_data['twitter'] != '' else None
            output['telegram'] = raw_data['telegram'] if raw_data['telegram'] != '' else None
            output['discord'] = raw_data['discord'] if raw_data['discord'] != '' else None

            return output
        else:
            raise HTTPException(status_code=500, detail=f"An error occurred with the Etherscan API: {data['message']}.")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"A request exception occurred: {e}.")


async def post_token_socials(chain: ChainEnum, token_address: str):
    """
    Post the token social information for a given token address on a given blockchain retrieved from an external API.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Raises:__
    - **400 Bad Request**: If the token address is invalid.
    - **500 Internal Server Error**: If an error occurred during the call to the external API.
    """
    validate_token_address(token_address)
    _token_address = token_address.lower()

    if token_metadata[chain.value][_token_address].name is None:
        try:
            info = await get_block_explorer_data(_token_address)

            for key, value in info.items():
                await patch_token_metadata(chain, _token_address, key, value)

            await patch_token_metadata(chain, _token_address, 'lastUpdatedTimestamp', int(time.time()))

            return token_metadata[chain.value][_token_address]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unknown error occurred during the call to fetch token info for {_token_address} on chain {chain.value}")

    return token_metadata[chain.value][_token_address]


async def post_token_liquidity_info(chain: ChainEnum, token_address: str):
    """
    Post the latest liquidity information for a given token address on a given blockchain. This information is queried directly from GoPlus Labs endpoints for token contract security.

    This endpoint will update the following entries:
    - **dex_liquidity_usd**: The latest liquidity information for the token.
    - **buy_tax**: The latest buy tax information for the token.
    - **sell_tax**: The latest sell tax information for the token.
    - **deployer**: The address of the deployer of the token contract.
    - **holder_count**: The number of holders of the token contract.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    """
    validate_token_address(token_address)
    _token_address = token_address.lower()

    if token_metadata[chain.value][_token_address].contractDeployer is None:
        try:
            url = f'https://api.gopluslabs.io/api/v1/token_security/{CHAIN_ID_MAPPING[chain.value]}'

            params = {
                'contract_addresses': _token_address
            }

            request_response = requests.get(url, params=params)
            request_response.raise_for_status()
            
            if request_response.status_code == 200:
                data = request_response.json()

                await patch_token_metadata(chain, _token_address, 'contractDeployer', data['result'][_token_address]['creator_address'])
                await patch_token_metadata(chain, _token_address, 'holders', int(data['result'][_token_address]['holder_count']))
                await patch_token_metadata(chain, _token_address, 'buyTax', 100 * float(data['result'][_token_address]['buy_tax']))
                await patch_token_metadata(chain, _token_address, 'sellTax', 100 * float(data['result'][_token_address]['sell_tax']))

                # Liquidity token calculations
                liquidityUsd = sum([float(item['liquidity']) for item in data['result'][_token_address]['dex']])

                # TODO: Fix these calculations from GoPlus API
                # lockedLiquidityUsd = sum([float(item['liquidity']) for item in data['result'][_token_address]['dex'] if item['locked'] == 'true'])
                # burnedLiquidityUsd = sum([float(item['liquidity']) for item in data['result'][_token_address]['dex'] if item['burned'] == 'true'])

                await patch_token_metadata(chain, _token_address, 'liquidityUsd', liquidityUsd)
                # await patch_token_metadata(chain, _token_address, 'lockedLiquidityUsd', lockedLiquidityUsd)
                # await patch_token_metadata(chain, _token_address, 'burnedLiquidityUsd', burnedLiquidityUsd)
            else:
                raise HTTPException(status_code=500, detail=f"An unknown error occurred during the call to fetch token security information for {_token_address} on chain {chain.value}.")

            await patch_token_metadata(chain, _token_address, 'lastUpdatedTimestamp', time.time())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unknown error occurred during the call to fetch token security information for {_token_address} on chain {chain.value}. {e}")
    
    return token_metadata[chain.value][_token_address]


async def post_token_logo_info(chain: ChainEnum, token_address: str):
    validate_token_address(token_address)
    _token_address = token_address.lower()

    if _token_address not in token_metadata[chain.value]:
        await initialize_token_metadata(chain.value, _token_address)

    if token_metadata[chain.value][_token_address].logoUrl is None:
        if tokens.get(_token_address):
            await patch_token_metadata(chain.value, token_address, 'logoUrl', tokens[_token_address]['logoURI'])

        # TODO: Add link to randomly generated rug.ai icon
    return token_metadata[chain.value][token_address]


async def post_token_contract_info(chain: ChainEnum, token_address: str):
    """
    Fetches the contract information for a given token address on a given blockchain.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    """
    validate_token_address(token_address)

    if mapping is None:
        raise HTTPException(status_code=500, detail=f"Failed to load labels from static file.")
    
    _token_address = token_address.lower()

    if _token_address not in contract_info[chain.value]:
        try:
            url = f'https://api.gopluslabs.io/api/v1/token_security/{CHAIN_ID_MAPPING[chain.value]}'

            params = {
                'contract_addresses': _token_address
            }

            request_response = requests.get(url, params=params)
            request_response.raise_for_status()
            
            if request_response.status_code == 200:
                data = request_response.json()

                data_response = data['result'][_token_address]

                items = []

                for key, item in mapping.items():
                    if key in data_response:
                        if key == 'owner_address':
                            item = ContractItem(
                                title=item['title'],
                                section=item['section'],
                                generalDescription=item['description'],
                                description=item['false_description'] if data_response[key] == '' else item['true_description'],
                                value=0 if data_response[key] == '' else 1,
                                severity=item['severity']
                            )
                        else:
                            item = ContractItem(
                                title=item['title'],
                                section=item['section'],
                                generalDescription=item['description'],
                                description=item['false_description'] if bool(data_response[key]) else item['true_description'],
                                value=float(data_response[key]) if data_response[key] != '' else None,
                                severity=item['severity']
                            )

                        items.append(item)

                contract_info[chain.value][_token_address] = ContractResponse(items=items)
            else:
                raise HTTPException(status_code=500, detail=f"Failed to fetch token security information from GoPlus: {request_response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch token security information from GoPlus: {e}")

    return contract_info[chain.value][_token_address]


async def post_score_info(chain: ChainEnum, token_address: str):
    validate_token_address(token_address)
    _token_address = token_address.lower()

    if _token_address not in score_mapping[chain.value]:
        score_mapping[chain.value][_token_address] = get_random_score()

    return score_mapping[chain.value][_token_address]


@router.get("/review/{chain}/{token_address}", response_model=TokenReviewResponse)
async def get_token_detailed_review(chain: ChainEnum, token_address: str): 
    validate_token_address(token_address)
    contract_info = await post_token_contract_info(chain, token_address)

    ai_comments = [AIComment(commentType="Function", title="Transferrss", description="This function is used to transfer tokens from one address to another."), 
                   AIComment(commentType="Function", title="SetSellFeue", description="This function is used to set the sell fee.")]

    return TokenReviewResponse(contractInfo=contract_info, aiComments=ai_comments, clusters=ClusterResponse(clusters=[[Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=322, percentage=0.12)], [Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=645, percentage=0.12), Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=5, percentage=0.12)], [Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=45, percentage=0.02)], [Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=300, percentage=0.05)], [Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=300, percentage=0.03)]]))


async def post_token_metadata(chain: ChainEnum, token_address: str):
    validate_token_address(token_address)
    _token_address = token_address.lower()

    if _token_address not in token_metadata[chain.value]:
        await initialize_token_metadata(chain, _token_address)

    await post_token_socials(chain, _token_address)
    await post_token_liquidity_info(chain, _token_address)
    await post_token_logo_info(chain, _token_address)

    # TODO: Fix this patching with correct Chain object
    # await patch_token_metadata(chain, _token_address, 'chain', CHAIN_ID_MAPPING[chain_id])

    return token_metadata[chain.value][_token_address]


async def post_token_info(chain: ChainEnum, token_address: str):
    """
    Post the latest information for a given token address on a given blockchain.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    """
    validate_token_address(token_address)
    _token_address = token_address.lower()

    tokenMetadata = await post_token_metadata(chain, token_address)
    score = await post_score_info(chain, _token_address)

    description = '''
    rug.ai AI-tooling identified **7** potential vulnerabilities in the **Wetch.ai** contract which could cause partial or complete loss of funds. Therefore, we recommend proceeding with caution when interacting with this contract.

    In Line 7, there is a `TransferOwnership` function which allows the ownership of the contract to be transferred to a malicious owner.
    '''

    # TODO: Refactor this to constants so it is easily modifiable
    aiSummary = AISummary(description=description, numIssues=7)
    topHolders = ClusterResponse(clusters=[[Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=322, percentage=0.12)], [Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=645, percentage=0.12), Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=5, percentage=0.12)], [Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=45, percentage=0.02)], [Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=300, percentage=0.05)], [Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=300, percentage=0.03)]])

    return TokenInfoResponse(tokenMetadata=tokenMetadata, score=score, aiSummary=aiSummary, topHolders=topHolders)


@router.get("/info/{chain}/{token_address}", response_model=TokenInfoResponse)
async def get_token_info(chain: ChainEnum, token_address: str):
    """
    Get the token information for a given token address on a given blockchain.

    __Parameters:__
    - **chain_id** (int): ID of the blockchain that the token belongs to.
    - **token_address** (str): The token address to query on the given blockchain.

    __Raises:__
    - **400 Bad Request**: If the chain ID is not supported.
    - **400 Bad Request**: If the token address is invalid.
    - **404 Not Found**: If the token address has never been updated and the token information does not exist.
    """
    validate_token_address(token_address)
    _token_address = token_address.lower()
    return await post_token_info(chain, _token_address)
