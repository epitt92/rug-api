from fastapi import HTTPException

def validate_token_address(token_address: str):
    if len(token_address) != 42:
        raise InvalidTokenAddressException(token_address)
    if not token_address.startswith('0x'):
        raise InvalidTokenAddressException(token_address)


class InvalidTokenAddressException(Exception):
    def __init__(self, token_address: str):
        super()._init__(token_address)
