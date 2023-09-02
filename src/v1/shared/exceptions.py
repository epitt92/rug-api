from fastapi import HTTPException

def validate_token_address(token_address: str):
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is not valid.")

    if not token_address.startswith('0x'):
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is not valid.")
