from fastapi import APIRouter
from fastapi.responses import JSONResponse
from botocore.exceptions import ClientError

from src.v1.referral.constants import DEFAULT_NUMBER_OF_USES
from src.v1.referral.dependencies import (
    is_referral_valid,
    generate_referral_code,
    is_referral_exists,
)
from src.v1.referral.schemas import ReferralUser, UsersEntry

from src.v1.shared.DAO import DAO
from src.v1.shared.exceptions import (
    DatabaseInsertFailureException,
    DatabaseLoadFailureException,
)

router = APIRouter()

USERS_DAO = DAO("users")
REFERRAL_CODE_DAO = DAO("referralcodes")


@router.get("/valid", include_in_schema=True)
async def is_referral_valid(referral_code: str):
    """
    Informs the caller whether a given referral code is valid or not.
    """
    validity = is_referral_valid(referral_code)

    status_code = 200 if validity else 400
    return JSONResponse(
        status_code=status_code, content={"status_code": status_code, "valid": validity}
    )


async def create_user(user: str):
    """
    Creates a new user in the database with the given email address.
    """
    # First calls generate_referral_code() to generate a new referral code
    code = generate_referral_code()

    # Adds a new row to `referralcodes` by instantiating a new ReferralUser object with the referral code and the user
    referral_entry = ReferralUser(referralCode=code, user=user)

    referral_entry_db = referral_entry.dict()

    # Generates a new UsersEntry object with the user, the referral code, and an empty list of referrals
    user_entry = UsersEntry(
        user=user,
        referralCode=code,
        referrals=[],
        totalReferrals=DEFAULT_NUMBER_OF_USES,
    )

    user_entry_db = user_entry.dict()

    # Adds a new row to `users` by instantiating a new UsersEntry object with the user, the referral code, and an empty list of referrals
    try:
        USERS_DAO.put(user_entry_db)
        REFERRAL_CODE_DAO.put(referral_entry_db)
    except ClientError as _:
        raise DatabaseInsertFailureException(
            message=f"Exception: Boto3 exception whilst fetching data from 'users' with PK: {user}"
        )
    except Exception as _:
        raise DatabaseInsertFailureException(
            message=f"Exception: Unknown exception whilst fetching data from 'users' with PK: {user}"
        )

    return JSONResponse(
        status_code=200,
        content={"status_code": 200, "detail": f"Successfully created user {user}."},
    )


async def referral_code_use(code: str, user: str):
    """
    Uses a referral code that belongs to a specific user.

    Note: This should check DynamoDB for a list of all valid referral codes to see if one exists, and if so, should replace it with a new row indicating how many invites that code has left.

    Note: Manual insertions into this table will allow the team to invite many people on a single referral code.
    """
    # First, calls is_referral_valid() to check whether the referral code exists and is valid
    if not is_referral_valid(code):
        return JSONResponse(
            status_code=400,
            content={"detail": f"Referral code {code} is invalid or does not exist."},
        )

    # Then pulls the referral code user using is_referral_exists() with return_bool=False
    referral_owner = is_referral_exists(code, return_bool=False)

    # Fetches the user data from `users` and modifies it:
    # Instantiates a new Referral object with the invitedUser set to the user who used the referral code, and confirmed set to True
    try:
        user_data = USERS_DAO.find_most_recent_by_pk(referral_owner)
    except ClientError as _:
        raise DatabaseLoadFailureException(
            message=f"Exception: Boto3 exception whilst fetching data from 'users' with PK: {referral_owner}"
        )
    except Exception as _:
        raise DatabaseLoadFailureException(
            message=f"Exception: Unknown exception whilst fetching data from 'users' with PK: {referral_owner}"
        )

    # Adds the new Referral object to the list of referrals for the user who owns the referral code
    user_data["referrals"].append({"invitedUser": user, "confirmed": True})

    # Instantiates a new UsersEntry object with the user who owns the referral code, the referral code itself, and the list of referrals
    user_entry = UsersEntry(**user_data)

    # Puts the new users entry into the database at the slot of the previous one
    try:
        USERS_DAO.put(user_entry.dict())
    except ClientError as _:
        raise DatabaseInsertFailureException(
            message=f"Exception: Boto3 exception whilst fetching data from 'users' with PK: {referral_owner}"
        )
    except Exception as _:
        raise DatabaseInsertFailureException(
            message=f"Exception: Unknown exception whilst fetching data from 'users' with PK: {referral_owner}"
        )

    # Calls create_user to create a new UsersEntry object for the user who used the referral code
    await create_user(user)

    return JSONResponse(
        status_code=200,
        content={"detail": f"Successfully used referral code {code} for user {user}."},
    )
