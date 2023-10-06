from pydantic import BaseModel, EmailStr, root_validator, validator
from typing import Optional, Union
import logging

from src.v1.feeds.exceptions import InvalidEventHash

from src.v1.shared.models import ChainEnum
from src.v1.shared.models import validate_token_address

import re

class EventClick(BaseModel):
    event_hash: str

    @validator('event_hash')
    def validate_event_id(cls, v):
        pattern = r'^0x[a-fA-F0-9]{12}$'
        if not re.match(pattern, v):
            logging.error(f"Raising InvalidEventHash exception for event_id: {v}")
            raise InvalidEventHash(event_hash=v, message=f"The string '{v}' does not match the required format: '0x' followed by 12 digits")
        return v


class TokenView(BaseModel):
    chain: ChainEnum
    token_address: str

    @root_validator(pre=True)
    def pre_process(cls, values):
        values['token_address'] = values['token_address'].lower()
        return values
    
    @validator('token_address')
    def validate_token_address(cls, value):
        return validate_token_address(value)
    