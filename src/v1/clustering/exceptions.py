from src.v1.clustering.constants import INVALID_ADDRESS_LENGTH, INVALID_ADDRESS_PREFIX, ADDRESS_LENGTH

class InvalidAddressLength(Exception):
    def __init__(self, message=INVALID_ADDRESS_LENGTH):
        super().__init__(message)

class InvalidAddressPrefix(Exception):
    def __init__(self, message=INVALID_ADDRESS_PREFIX):
        super().__init__(message)

def validate_token_address(token_address: str):
    if len(token_address) != ADDRESS_LENGTH:
        raise InvalidAddressLength()
    if not token_address.startswith('0x'):
        raise InvalidAddressPrefix()
