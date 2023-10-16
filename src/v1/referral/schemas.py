# import time
# from pydantic import BaseModel, EmailStr, constr, root_validator, validator
# from typing import Optional, List, Union


# class ReferralCodeUse(BaseModel):
#     username: EmailStr
#     timestamp: int

#     @root_validator(pre=True)
#     def pre_process(cls, values):
#         values['username'] = values['username'].lower()
#         values['timestamp'] = int(time.time())
#         return values


# # Response model for a row from the 'referralcodes' table
# class ReferralCode(BaseModel):
#     code: str # Primary Key
#     expiry: int
#     initialUses: int

#     uses: List[ReferralCodeUse]

#     numberUses: int
#     usesRemaining: int

#     @root_validator(pre=True)
#     def pre_process(cls, values):
#         values['code'] = values['code'].lower()

#         values['numberUses'] = len(values['uses']) if values.get('uses') else 0
#         values['usesRemaining'] = values['initialUses'] - values['numberUses']

#         return values


# # Response model for GET /get_referral_code endpoint
# class UserReferralData(BaseModel):
#     username: EmailStr
#     referralCode: str
#     previousReferralCodes: List[ReferralCode]

#     @root_validator(pre=True)
#     def pre_process(cls, values):
#         values['username'] = values['username'].lower()
#         return values
