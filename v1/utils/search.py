from core.models import SearchResponse, Chain, Token

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
    logoUrl=None,
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
    score=97.2,
    deployedAgo=23324,
    refreshedAgo=122,
    chain=ethereum
)

shiba_inu = Token(
    name="Shiba Inu",
    symbol="SHIB",
    tokenAddress="0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce",
    score=43.9,
    chain=ethereum,
    deployedAgo=2434323,
    refreshedAgo=32332
)

pepe = Token(
    name="PEPE",
    symbol="PEPE",
    tokenAddress="0x6982508145454ce325ddbe47a25d4ec3d2311933",
    score=23.2,
    chain=ethereum,
    deployedAgo=23324,
    refreshedAgo=122
)

harry_potter_obama_sonic_10_inu = Token(
    name="HarryPotterObamaSonic10Inu",
    symbol="BITCOIN",
    tokenAddress="0x9343e24716659a3551eb10aff9472a2dcad5db2d",
    score=73.2,
    chain=ethereum,
    deployedAgo=23324,
    refreshedAgo=122
)

# Search Response

search_response = SearchResponse(
    tokens=[stfx, shiba_inu, pepe, harry_potter_obama_sonic_10_inu]
    )
