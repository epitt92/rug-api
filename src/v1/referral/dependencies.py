import re, random, boto3
from fastapi import HTTPException
from botocore.client import ClientError
from pydantic import EmailStr
from typing import Union

from src.v1.shared.DAO import DAO
from src.v1.shared.exceptions import DatabaseLoadFailureException

from src.v1.auth.exceptions import InvalidReferralCodeFormat

REFERRAL_CODE_DAO = DAO("referralcodes")
USERS_DAO = DAO("users")


def generate_hex_string(length=6):
    # Generate a random hexadecimal string of the specified length
    return "".join(random.choice("0123456789abcdef") for _ in range(length))


def has_invites(user: EmailStr) -> bool:
    """
    Checks whether a given user has any invites remaining by querying the `users` table.
    """
    try:
        user_data = USERS_DAO.find_most_recent_by_pk(user)
    except ClientError as _:
        raise DatabaseLoadFailureException(
            message=f"Exception: Boto3 exception whilst fetching data from 'users' with PK: {user}"
        )
    except Exception as _:
        raise DatabaseLoadFailureException(
            message=f"Exception: Unknown exception whilst fetching data from 'users' with PK: {user}"
        )

    if user_data:
        if user_data.get("referralsRemaining") and user_data.get("referralIsValid"):
            return (user_data.get("referralsRemaining") > 0) and (
                user_data.get("referralIsValid") == True
            )
        else:
            return False
    else:
        return False


def is_referral_valid(referral_code: str) -> bool:
    """
    Informs the caller whether a given referral code is valid or not.
    """
    # Calls is_referral_exists() with return_bool=False to get the user to which the referral code belongs
    user = is_referral_exists(referral_code, return_bool=False)

    # If the referral code exists, check whether the user has any invites remaining
    return has_invites(user) if user else False


def is_referral_exists(
    referral_code: str, return_bool: bool = True
) -> Union[bool, str]:
    """
    Checks whether a given `referral_code` exists in the database.

    If `return_bool` is True, returns a boolean value indicating whether the referral code exists.
    If `return_bool` is False, returns the user to which the referral code belongs if it exists, otherwise returns None.

    Raises an InvalidReferralCodeFormat exception if the referral code is not in the correct format.
    """
    # Check whether the referral code is in the correct format
    if not re.match("^[a-f0-9]{6}$", referral_code):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid referral code format. Referral code must be a hexadecimal string of length 6.",
        )

    # Check whether the referral code exists in the database
    try:
        referral_code_data = REFERRAL_CODE_DAO.find_by_pk(referral_code)
    except ClientError as _:
        raise DatabaseLoadFailureException(
            message=f"Exception: Boto3 exception whilst fetching data from 'referralcodes' with PK: {referral_code}"
        )
    except Exception as _:
        raise DatabaseLoadFailureException(
            message=f"Exception: Unknown exception whilst fetching data from 'referralcodes' with PK: {referral_code}"
        )

    if referral_code_data and referral_code_data.get("user"):
        return True if return_bool else referral_code_data.get("user")
    else:
        return False if return_bool else None


def generate_referral_code() -> str:
    code = generate_hex_string(length=6)

    success = False
    while not success:
        # Do requisite checks to ensure that the referral code is unique
        exists = is_referral_exists(code)
        if not exists:
            success = True
        else:
            code = generate_hex_string(length=6)
            continue

    return code
