import random, logging
from typing import Union

from src.v1.shared.constants import *
from src.v1.shared.schemas import ScoreResponse, Score
from src.v1.shared.models import ChainEnum
from src.v1.shared.schemas import Chain

def get_chain(chain: ChainEnum):
    _chain = str(chain.value) if isinstance(chain, ChainEnum) else str(chain)

    if _chain == 'ethereum':
        return Chain(chainId=ETHEREUM_CHAIN_ID)
    elif _chain == 'arbitrum':
        return Chain(chainId=ARBITRUM_CHAIN_ID)
    elif _chain == 'base':
        logging.info(f"Returning base chain: {BASE_CHAIN_ID}")
        return Chain(chainId=BASE_CHAIN_ID)
    else:
        raise ValueError(f"Invalid chain: {_chain}")

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
