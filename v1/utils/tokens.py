from core.models import SearchResponse, Chain, Token, ReelResponse, ScoreResponse, Score
import random

# Blockchains

arbitrum = Chain(
    chainId=42161,
    name="Arbitrum One",
    logoUrl=None,
    nativeAsset="ETH"
)

ethereum = Chain(
    chainId=1,
    name="Ethereum",
    logoUrl="https://tokens.1inch.io/0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee.png",
    nativeAsset="ETH"
)

bnb_chain = Chain(
    chainId=56,
    name="Binance Smart Chain",
    logoUrl=None,
    nativeAsset="BNB"
)

# Tokens

stfx = Token(
    name="STFX",
    symbol="STFX",
    tokenAddress="0x9343e24716659a3551eb10aff9472a2dcad5db2d",
    score=ScoreResponse(overallScore=int(random.randint(0, 100)), 
                        liquidityScore=Score(value=int(random.randint(0, 100)), description="No liquidity vulnerabilities found"), 
                        transferrabilityScore=Score(value=int(random.randint(0, 100)), description="The token cannot be sold"), 
                        supplyScore=Score(value=int(random.randint(0, 100)), description="The token supply is modifiable")),
    deployedAgo=23324,
    chain=ethereum
)

shiba_inu = Token(
    name="Shiba Inu",
    symbol="SHIB",
    tokenAddress="0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce",
    score=ScoreResponse(overallScore=int(random.randint(0, 100)), 
                        liquidityScore=Score(value=int(random.randint(0, 100)), description="No liquidity vulnerabilities found"), 
                        transferrabilityScore=Score(value=int(random.randint(0, 100)), description="The token cannot be sold"), 
                        supplyScore=Score(value=int(random.randint(0, 100)), description="The token supply is modifiable")),
    chain=ethereum,
    deployedAgo=2434323,
)

pepe = Token(
    name="PEPE",
    symbol="PEPE",
    tokenAddress="0x6982508145454ce325ddbe47a25d4ec3d2311933",
    score=ScoreResponse(overallScore=int(random.randint(0, 100)), 
                        liquidityScore=Score(value=int(random.randint(0, 100)), description="No liquidity vulnerabilities found"), 
                        transferrabilityScore=Score(value=int(random.randint(0, 100)), description="The token cannot be sold"), 
                        supplyScore=Score(value=int(random.randint(0, 100)), description="The token supply is modifiable")),
    chain=ethereum,
    deployedAgo=23324,
)

harry_potter_obama_sonic_10_inu = Token(
    name="HarryPotterObamaSonic10Inu",
    symbol="BITCOIN",
    tokenAddress="0x9343e24716659a3551eb10aff9472a2dcad5db2d",
    score=ScoreResponse(overallScore=int(random.randint(0, 100)), 
                        liquidityScore=Score(value=int(random.randint(0, 100)), description="No liquidity vulnerabilities found"), 
                        transferrabilityScore=Score(value=int(random.randint(0, 100)), description="The token cannot be sold"), 
                        supplyScore=Score(value=int(random.randint(0, 100)), description="The token supply is modifiable")),
    chain=ethereum,
    deployedAgo=23324,
)

psyop = Token(
    name="Psyop",
    symbol="PSYOP",
    tokenAddress="0x3007083eaa95497cd6b2b809fb97b6a30bdf53d3",
    score=ScoreResponse(overallScore=int(random.randint(0, 100)), 
                        liquidityScore=Score(value=int(random.randint(0, 100)), description="No liquidity vulnerabilities found"), 
                        transferrabilityScore=Score(value=int(random.randint(0, 100)), description="The token cannot be sold"), 
                        supplyScore=Score(value=int(random.randint(0, 100)), description="The token supply is modifiable")),
    chain=ethereum,
    deployedAgo=9048,
)

saudi_raptor = Token(
    name="SAUDI RAPTOR",
    symbol="SAUDIRAPTOR",
    tokenAddress="0x0B061f618D3e27B9Ac8eE6AB4B7211DB221544d7",
    score=ScoreResponse(overallScore=int(random.randint(0, 100)), 
                        liquidityScore=Score(value=int(random.randint(0, 100)), description="No liquidity vulnerabilities found"), 
                        transferrabilityScore=Score(value=int(random.randint(0, 100)), description="The token cannot be sold"), 
                        supplyScore=Score(value=int(random.randint(0, 100)), description="The token supply is modifiable")),
    chain=ethereum,
    deployedAgo=3232,
)

gmx = Token(
    name="GMX",
    symbol="GMX",
    tokenAddress="0xfc5a1a6eb076a2c7ad06ed22c90d7e710e35ad0a",
    score=ScoreResponse(overallScore=int(random.randint(0, 100)), 
                        liquidityScore=Score(value=int(random.randint(0, 100)), description="No liquidity vulnerabilities found"), 
                        transferrabilityScore=Score(value=int(random.randint(0, 100)), description="The token cannot be sold"), 
                        supplyScore=Score(value=int(random.randint(0, 100)), description="The token supply is modifiable")),
    chain=arbitrum,
    deployedAgo=212121,
)

magic = Token(
    name="MAGIC",
    symbol="MAGIC",
    tokenAddress="0x539bdE0d7Dbd336b79148AA742883198BBF60342",
    sscore=ScoreResponse(overallScore=int(random.randint(0, 100)), 
                        liquidityScore=Score(value=int(random.randint(0, 100)), description="No liquidity vulnerabilities found"), 
                        transferrabilityScore=Score(value=int(random.randint(0, 100)), description="The token cannot be sold"), 
                        supplyScore=Score(value=int(random.randint(0, 100)), description="The token supply is modifiable")),
    chain=arbitrum,
    deployedAgo=3232,
)

spell = Token(
    name="Spell Token",
    symbol="SPELL",
    tokenAddress="0x090185f2135308bad17527004364ebcc2d37e5f6",
    score=ScoreResponse(overallScore=int(random.randint(0, 100)), 
                        liquidityScore=Score(value=int(random.randint(0, 100)), description="No liquidity vulnerabilities found"), 
                        transferrabilityScore=Score(value=int(random.randint(0, 100)), description="The token cannot be sold"), 
                        supplyScore=Score(value=int(random.randint(0, 100)), description="The token supply is modifiable")),
    chain=ethereum,
    deployedAgo=3232,
)

tron = Token(
    name="TRON",
    symbol="TRX",
    tokenAddress="0xCE7de646e7208a4Ef112cb6ed5038FA6cC6b12e3",
    score=ScoreResponse(overallScore=int(random.randint(0, 100)), 
                        liquidityScore=Score(value=int(random.randint(0, 100)), description="No liquidity vulnerabilities found"), 
                        transferrabilityScore=Score(value=int(random.randint(0, 100)), description="The token cannot be sold"), 
                        supplyScore=Score(value=int(random.randint(0, 100)), description="The token supply is modifiable")),
    chain=bnb_chain,
    deployedAgo=3232,
)

yearn = Token(
    name="yearn.finance",
    symbol="YFI",
    tokenAddress="0x0bc529c00c6401aef6d220be8c6ea1667f6ad93e",
    score=ScoreResponse(overallScore=int(random.randint(0, 100)), 
                        liquidityScore=Score(value=int(random.randint(0, 100)), description="No liquidity vulnerabilities found"), 
                        transferrabilityScore=Score(value=int(random.randint(0, 100)), description="The token cannot be sold"), 
                        supplyScore=Score(value=int(random.randint(0, 100)), description="The token supply is modifiable")),
    chain=ethereum,
    deployedAgo=3232,
)

# Search Response

search_response = SearchResponse(items=[stfx, shiba_inu, pepe, harry_potter_obama_sonic_10_inu])

# Token Reel

reel_response = ReelResponse(items=[tron, yearn, magic, psyop, gmx, shiba_inu, pepe, saudi_raptor])
