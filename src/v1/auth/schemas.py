from pydantic import BaseModel, EmailStr, constr, root_validator, validator
from typing import Optional
from web3 import Web3

import re


class EmailAccountBase(BaseModel):
    username: EmailStr

    @root_validator(pre=True)
    def pre_process(cls, values):
        values["username"] = values["username"].lower()
        return values


class CreateEmailAccount(EmailAccountBase):
    password: constr(min_length=10)
    referral_code: str

    @validator("referral_code")
    def referral_code_is_valid(cls, v):
        # Check if the referral code is a 6 digit hexadecimal string
        valid = bool(re.match(r"^[a-fA-F0-9]{6}$", v))
        if not valid:
            raise ValueError("Referral code must be a hexadecimal string of length 6.")
        return v


class SignInEmailAccount(EmailAccountBase):
    password: constr(min_length=10)


class VerifyEmailAccount(BaseModel):
    username: EmailStr
    password: constr(min_length=10)
    referral_code: str
    confirmation_code: str

    @root_validator(pre=True)
    def pre_process(cls, values):
        values["username"] = values["username"].lower()
        return values

    @validator("confirmation_code")
    def confirmation_code_is_valid(cls, v):
        valid = bool(re.match(r"^\d{6}$", v))
        if not valid:
            raise ValueError("Confirmation code must be a 6-digit number.")
        return v

    @validator("referral_code")
    def referral_code_is_valid(cls, v):
        # Check if the referral code is a 6 digit hexadecimal string
        valid = bool(re.match(r"^[a-fA-F0-9]{6}$", v))
        if not valid:
            raise ValueError("Referral code must be a hexadecimal string of length 6.")
        return v


class ResetPassword(EmailAccountBase):
    new_password: constr(min_length=10)
    verification_code: str


class CreateNewPasswordToken(BaseModel):
    username: EmailStr


class SignedMessage(BaseModel):
    address: constr(min_length=42, max_length=42)
    signature: constr(min_length=132, max_length=132)
    message: constr(min_length=1)

    @root_validator(pre=True)
    def pre_process(cls, values):
        values["address"] = values["address"].lower()
        return values

    @validator("address")
    def address_is_valid(cls, v):
        valid = bool(re.match(r"^0x[a-fA-F0-9]{40}$", v))
        if not valid:
            raise ValueError("Address must be a valid Ethereum address.")
        return v


class UserAccessTokens(BaseModel):
    accessToken: str
    refreshToken: str
