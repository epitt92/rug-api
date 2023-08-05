import random

from src.v1.shared.schemas import ScoreResponse, Score

def get_random_score(supply_score, supply_description, transferrability_score, transferrability_description):
    output = ScoreResponse(
                overallScore=float(random.uniform(0, 100)), 
                liquidityScore=Score(value=float(random.uniform(0, 100)), description="No liquidity description available."),
                transferrabilityScore=Score(value=transferrability_score, description=transferrability_description), 
                supplyScore=Score(value=supply_score, description=supply_description),
                )
    
    return output
