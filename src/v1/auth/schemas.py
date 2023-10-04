from pydantic import BaseModel, EmailStr, constr, root_validator, validator
from typing import Optional
from web3 import Web3

import re

class EmailAccountBase(BaseModel):
    username: EmailStr

    @root_validator(pre=True)
    def pre_process(cls, values):
        values['username'] = values['username'].lower()
        return values


class CreateEmailAccount(EmailAccountBase):
    password: constr(min_length=10)
    referral_code: str

    @validator('referral_code')
    def referral_code_is_valid(cls, v):
        # TODO: Must check if the referral code is valid
        return v


class SignInEmailAccount(EmailAccountBase):
    password: constr(min_length=10)


class VerifyEmailAccount(BaseModel):
    username: EmailStr
    confirmation_code: str
    
    @root_validator(pre=True)
    def pre_process(cls, values):
        values['username'] = values['username'].lower()
        return values
    
    @validator('confirmation_code')
    def confirmation_code_is_valid(cls, v):
        valid = bool(re.match(r"^\d{6}$", v))
        if not valid:
            raise ValueError('Confirmation code must be a 6-digit number.')
        return v


class ResetPassword(EmailAccountBase):
    new_password: constr(min_length=10)
    verification_code: str


class CreateNewPasswordToken(BaseModel):
    username: EmailStr

#########

class SignedMessage(BaseModel):
    address: constr(min_length=42, max_length=42)
    signature: constr(min_length=132, max_length=132)
    message: constr(min_length=1)

    @root_validator(pre=True)
    def pre_process(cls, values):
        values["address"] = values["address"].lower()
        return values
    
    @validator('address')
    def address_is_valid(cls, v):
        valid = bool(re.match(r"^0x[a-fA-F0-9]{40}$", v))
        if not valid:
            raise ValueError('Address must be a valid Ethereum address.')
        return v 


class CreateWeb3Account(BaseModel):
    # ECDSA signature parameters
    signed_message: SignedMessage

    referral_code: str
 
    # Generated dynamically at instantiation
    username: Optional[str]
    password: Optional[str]

    @root_validator(pre=True)
    def pre_process(cls, values):        
        if isinstance(values['signed_message'], dict):
            address = values['signed_message'].get('address')
        else:
            address = values['signed_message'].address

        values['username'] = address
        values['password'] = Web3.keccak(text=address).hex()
        return values

    @validator('referral_code')
    def referral_code_is_valid(cls, v):
        # TODO: Must check if the referral code is valid
        return v


class SignInWeb3Account(BaseModel):
    signed_message: SignedMessage

#########
# responses

class UserAccessTokens(BaseModel):
    accessToken: str
    refreshToken: str
