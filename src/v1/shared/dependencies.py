import random
from typing import Union

from src.v1.shared.schemas import ScoreResponse, Score
from src.v1.shared.models import ChainEnum

def get_random_score():
    output = ScoreResponse(
                overallScore=float(random.uniform(0, 100)), 
                liquidityScore=Score(value=float(random.uniform(0, 100)), description="No liquidity description available."), 
                transferrabilityScore=Score(value=float(random.uniform(0, 100)), description="No transferrability description available."), 
                supplyScore=Score(value=float(random.uniform(0, 100)), description="No supply description available.")
                )
    
    return output

def get_primary_key(token_address: str, chain: Union[str, ChainEnum]) -> str:
    if isinstance(chain, ChainEnum):
        return f"{token_address.lower()}_{str(chain.value)}"
    else:
        return f"{token_address.lower()}_{str(chain)}"
