from pydantic import BaseModel, EmailStr, constr, root_validator, validator
from typing import Optional

class CreateEmailAccount(BaseModel):
    username: EmailStr
    password: constr(min_length=10)
    referral_code: str

    @root_validator(pre=True)
    def pre_process(cls, values):
        values['username'] = values['username'].lower()
        return values


class CreateNewPassword(BaseModel):
    recovery_token: str
    password: constr(min_length=10)


class CreateNewPasswordToken(BaseModel):
    username: EmailStr


class ChangePassword(BaseModel):
    old_password: constr(min_length=10)
    new_password: constr(min_length=10)

#########

class CreateWeb3Account(BaseModel):
    username: constr(min_length=42, max_length=42)
    password: Optional[str]
