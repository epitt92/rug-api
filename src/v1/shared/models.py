from enum import Enum
from src.v1.shared.exceptions import InvalidTokenAddressException

class ChainEnum(Enum):
    ethereum = "ethereum"
    arbitrum = "arbitrum"
    base = "base"

def validate_token_address(token_address: str):
    if len(token_address) != 42:
        raise InvalidTokenAddressException()
    if not token_address.startswith('0x'):
        raise InvalidTokenAddressException()
    
    return token_address.lower()
