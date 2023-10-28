from fastapi import APIRouter
from fastapi.responses import JSONResponse
from botocore.exceptions import ClientError
import logging, time

from src.v1.referral.dependencies import generate_referral_code, check_if_referral_code_exists
from src.v1.referral.dependencies import is_referral_valid

from src.v1.shared.DAO import DAO

router = APIRouter()

@router.get("/valid", include_in_schema=True)
async def is_referral_valid(referral_code: str):
    """
    Informs the caller whether a given referral code is valid or not.
    """
    validity = is_referral_valid(referral_code)

    status_code = 200 if validity else 400
    return JSONResponse(status_code=status_code, content={"valid": validity})


async def create_user(user: str):
    """
    Creates a new user in the database with the given email address.
    """
    # First calls generate_referral_code() to generate a new referral code

    # Adds a new row to `referralcodes` by instantiating a new ReferralUser object with the referral code and the user

    # Generates a new UsersEntry object with the user, the referral code, and an empty list of referrals

    # Adds a new row to `users` by instantiating a new UsersEntry object with the user, the referral code, and an empty list of referrals

    return JSONResponse(status_code=200, content={"detail": f"Successfully created user {user}."})


# TODO: Add check that `user` exists in the database
@router.post("/use/{code}", include_in_schema=True)
async def post_referral_code_use(code: str, user: str):
    """
    Uses a referral code that belongs to a specific user.

    Note: This should check DynamoDB for a list of all valid referral codes to see if one exists, and if so, should replace it with a new row indicating how many invites that code has left.

    Note: Manual insertions into this table will allow the team to invite many people on a single referral code.
    """
    # First, calls is_referral_valid() to check whether the referral code exists and is valid

    # Then pulls the referral code user using is_referral_exists() with return_bool=False

    # Fetches the user data from `users` and modifies it:
    # Instantiates a new Referral object with the invitedUser set to the user who used the referral code, and confirmed set to True

    # Adds the new Referral object to the list of referrals for the user who owns the referral code

    # Instantiates a new UsersEntry object with the user who owns the referral code, the referral code itself, and the list of referrals

    # Puts the new users entry into the database at the slot of the previous one

    # Calls create_user to create a new UsersEntry object for the user who used the referral code

    return JSONResponse(status_code=200, content={"detail": f"Successfully used referral code {code} for user {user}."})
