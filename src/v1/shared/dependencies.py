import random
from typing import Union

from src.v1.shared.constants import *
from src.v1.shared.schemas import ScoreResponse, Score
from src.v1.shared.models import ChainEnum
from src.v1.shared.schemas import Chain

def get_chain(chain: ChainEnum):
    _chain = str(chain.value) if isinstance(chain, ChainEnum) else str(chain)

    if _chain == 'ethereum':
        output = {
            'chainId': ETHEREUM_CHAIN_ID,
            'name': ETHEREUM_CHAIN_NAME,
            'logoUrl': ETHEREUM_LOGO_URL,
            'nativeAsset': ETHEREUM_NATIVE_ASSET,
        }
    elif _chain == 'bsc':
        output = {
            'chainId': BSC_CHAIN_ID,
            'name': BSC_CHAIN_NAME,
            'logoUrl': BSC_LOGO_URL,
            'nativeAsset': BSC_NATIVE_ASSET,
        }
    elif _chain == 'arbitrum':
        output = {
            'chainId': ARBITRUM_CHAIN_ID,
            'name': ARBITRUM_CHAIN_NAME,
            'logoUrl': ARBITRUM_LOGO_URL,
            'nativeAsset': ARBITRUM_NATIVE_ASSET,
        }
    elif _chain == 'base':
        output = {
            'chainId': BASE_CHAIN_ID,
            'name': BASE_CHAIN_NAME,
            'logoUrl': BASE_LOGO_URL,
            'nativeAsset': BASE_NATIVE_ASSET,
        }
    else:
        raise ValueError(f"Invalid chain: {_chain}")
    
    return Chain(**output)

def get_random_score(supply_score, supply_description, transferrability_score, transferrability_description):
    output = ScoreResponse(
                overallScore=float(random.uniform(0, 100)), 
                liquidityScore=Score(value=float(random.uniform(0, 100)), description="No liquidity description available."),
                transferrabilityScore=Score(value=transferrability_score, description=transferrability_description), 
                supplyScore=Score(value=supply_score, description=supply_description),
                )
    
    return output

def get_primary_key(token_address: str, chain: Union[str, ChainEnum]) -> str:
    if isinstance(chain, ChainEnum):
        return f"{token_address.lower()}_{str(chain.value)}"
    else:
        return f"{token_address.lower()}_{str(chain)}"
