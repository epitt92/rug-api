import json

MOST_VIEWED_TOKENS_STALENESS_THRESHOLD = 60 * 3  # 3 hours
MOST_VIEWED_TOKENS_LIMIT = 10
MOST_VIEWED_TOKENS_NUM_MINUTES = 60 * 60 * 6  # 6 hours
TOP_EVENTS_STALENESS_THRESHOLD = 60 * 60 * 3  # 3 hours
TOP_EVENTS_LIMIT = 5
TOP_EVENTS_NUM_MINUTES = 60 * 60 * 6  # 6 hours

with open("src/v1/shared/files/erc20.json", "r") as f:
    ERC20_ABI = json.load(f)

with open("src/v1/shared/files/uniswapv2.json", "r") as f:
    UNISWAP_V2_ABI = json.load(f)

with open("src/v1/shared/files/uniswapv3.json", "r") as f:
    UNISWAP_V3_ABI = json.load(f)

with open("src/v1/shared/files/metadataAnalytics.json", "r") as f:
    METADATA_ANALYTICS_ABI = json.load(f)

CHAIN_ID_MAPPING = {"ethereum": 1, "bsc": 56, "arbitrum": 42161, "base": 8453}
METADATA_ANALYTICS_ADDRESS = {
    "ethererum": "0x6D72Bd36957aDc6b1C1a3EaB657894066C07a934",
    "base": "0x6D72Bd36957aDc6b1C1a3EaB657894066C07a934",
}

SYMBOLS = {
    "ethereum": {
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": "ETH",
        "0xdac17f958d2ee523a2206206994597c13d831ec7": "USDT",
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "USDC",
        "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": "WBTC",
    },
    "base": {
        "0x4200000000000000000000000000000000000006": "ETH",
        "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA": "USDC",
        "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913": "USDC",
    },
}

POOL_INDEXER = {"ethereum": {}, "base": {}}
