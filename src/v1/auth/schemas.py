from pydantic import BaseModel, EmailStr, constr, root_validator, validator
from typing import Optional

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


class ChangePassword(BaseModel):
    old_password: constr(min_length=10)
    new_password: constr(min_length=10)

#########

class CreateWeb3Account(BaseModel):
    username: constr(min_length=42, max_length=42)
    password: Optional[str]


#########
# responses

class UserAccessTokens(BaseModel):
    accessToken: str
    refreshToken: str
    idToken: str
