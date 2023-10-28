import time
from pydantic import BaseModel, EmailStr, constr, root_validator, validator
from typing import Optional, List, Union

# referralcodes Table
# Enforce that a (PK) can only have one row in the table
class ReferralUser(BaseModel):
    referralCode: str # (PK)
    user: EmailStr # (SK)

# users Table
# Enforce that a (PK) can only have one row in the table
class Referral(BaseModel):
    invitedUser: EmailStr # Email address of the invited user
    timestamp: int # UNIX timestamp at which the invite was accepted
    confirmed: bool = True

    @root_validator(pre=True)
    def pre_process(cls, values):
        values['timestamp'] = int(time.time())
        return values

class UsersEntry(BaseModel):
    user: EmailStr # User who is inviting people (PK)
    referralCode: str # Referral code itself (SK)
    referrals: List[Referral] = []

    totalReferrals: int # Number of people the user is able to invite in total

    referralsRemaining: int # Calculated during pre-processing
    referralsUsed: int # Calculated during pre-processing

    referralIsValid: bool = True # Used to prevent further sign ups by this user's referral
    timeCreated: int

    @root_validator(pre=True)
    def validate_referrals(cls, values):
        if values.get('referrals'):
            accepted_referrals = []
            for item in values['referrals']:
                if isinstance(item, dict):
                    if item.get('confirmed') == True:
                        accepted_referrals.append(item)
                else:
                    if item.confirmed == True:
                        accepted_referrals.append(item)
            
            values['referralsRemaining'] = values['totalReferrals'] - len(accepted_referrals)
            values['referralsUsed'] = len(accepted_referrals)

        values['timeCreated'] = int(time.time())
        return values
