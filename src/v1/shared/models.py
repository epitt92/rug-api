from enum import Enum
from src.v1.shared.exceptions import InvalidTokenAddressException


class ChainEnum(Enum):
    ethereum = "ethereum"
    arbitrum = "arbitrum"
    base = "base"


class DexEnum(Enum):
    uniswapv2 = "uniswapv2"
    uniswapv3 = "uniswapv3"
    pancakeswapv2 = "pancakeswapv2"
    pancakeswapv3 = "pancakeswapv3"
    sushiswap = "sushiswap"
    baseswap = "baseswap"
    rocketswap = "rocketswap"
    traderjoe = "traderjoe"


def validate_token_address(token_address: str):
    if len(token_address) != 42:
        raise InvalidTokenAddressException()
    if not token_address.startswith("0x"):
        raise InvalidTokenAddressException()

    return token_address.lower()
