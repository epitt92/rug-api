from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from botocore.exceptions import ClientError
import logging, boto3

from src.v1.referral.constants import DEFAULT_NUMBER_OF_USES
from src.v1.referral.dependencies import (
    is_referral_valid_,
    generate_referral_code_,
    is_referral_exists_,
    render_template,
)
from src.v1.referral.schemas import ReferralUser, UsersEntry, Referral

from src.v1.shared.DAO import DAO
from src.v1.shared.exceptions import (
    DatabaseInsertFailureException,
    DatabaseLoadFailureException,
)

from src.v1.auth.dependencies import get_username_from_access_token

router = APIRouter()

USERS_DAO = DAO("userstemp", cache=False)
REFERRAL_CODE_DAO = DAO("referralcodestemp", cache=False)

ses = boto3.client("ses", region_name="eu-west-2")


@router.get("/valid", include_in_schema=True)
async def is_referral_valid(referral_code: str):
    """
    Informs the caller whether a given referral code is valid or not.
    """
    logging.info(f"Calling is_referral_valid with referral code {referral_code}...")

    validity = await is_referral_valid_(referral_code)

    status_code = 200 if validity else 400
    return JSONResponse(
        status_code=status_code, content={"status_code": status_code, "valid": validity}
    )


async def create_user(user: str):
    """
    Creates a new user in the database with the given email address.
    """
    logging.info(f"Calling create_user with user {user}...")

    # First calls generate_referral_code() to generate a new referral code
    code = await generate_referral_code_()

    logging.info(f"Generated referral code {code} for user {user}.")

    # Adds a new row to `referralcodes` by instantiating a new ReferralUser object with the referral code and the user
    referral_entry = ReferralUser(referral_code=code, username=user)

    referral_entry_db = referral_entry.dict()

    logging.info(f"Referral entry for user {user}: {referral_entry_db}")

    # Generates a new UsersEntry object with the user, the referral code, and an empty list of referrals
    user_entry = UsersEntry(
        username=user,
        referral_code=code,
        referrals=[],
        totalReferrals=DEFAULT_NUMBER_OF_USES,
    )

    user_entry_db = user_entry.dict()

    logging.info(f"User entry for user {user}: {user_entry_db}")

    # Adds a new row to `users` by instantiating a new UsersEntry object with the user, the referral code, and an empty list of referrals
    try:
        logging.info(f"Putting user entry for user {user} into database...")
        USERS_DAO.insert_new(user, user_entry_db)
        logging.info(f"Successfully put user entry for user {user} into database.")
        logging.info(f"Putting referral entry for user {user} into database...")
        REFERRAL_CODE_DAO.insert_new(code, referral_entry_db)
        logging.info(f"Successfully put referral entry for user {user} into database.")
    except ClientError as e:
        logging.error(e)
        raise DatabaseInsertFailureException(
            message=f"Exception: Boto3 exception whilst fetching data from 'users' with PK: {user}"
        )
    except Exception as e:
        logging.error(e)
        raise DatabaseInsertFailureException(
            message=f"Exception: Unknown exception whilst fetching data from 'users' with PK: {user}"
        )

    logging.info(f"Successfully created user {user}.")

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
    if not await is_referral_valid_(code):
        return JSONResponse(
            status_code=400,
            content={"detail": f"Referral code {code} is invalid or does not exist."},
        )

    logging.info(f"Referral code {code} is valid.")

    # Then pulls the referral code user using is_referral_exists() with return_bool=False
    referral_owner = await is_referral_exists_(code, return_bool=False)

    logging.info(f"Referral code {code} belongs to user {referral_owner}.")

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

    logging.info(f"User data for {referral_owner}: {user_data}")

    # Adds the new Referral object to the list of referrals for the user who owns the referral code
    referrals = user_data.get("referrals")

    referrals.append(Referral(invited_username=user, confirmed=True))
    user_data["referrals"] = referrals

    logging.info(
        f"User data for {referral_owner} after appending new referral: \n\n{user_data}"
    )

    # Instantiates a new UsersEntry object with the user who owns the referral code, the referral code itself, and the list of referrals
    user_entry = UsersEntry(**user_data)

    logging.info(f"User entry for {referral_owner}: \n\n{user_entry.dict()}")

    # Puts the new users entry into the database at the slot of the previous one
    try:
        USERS_DAO.insert_new(referral_owner, user_entry.dict())
    except ClientError as e:
        logging.error(e)

        raise DatabaseInsertFailureException(
            message=f"Exception: Boto3 exception whilst fetching data from 'users' with PK: {referral_owner}"
        )
    except Exception as e:
        logging.error(e)

        raise DatabaseInsertFailureException(
            message=f"Exception: Unknown exception whilst fetching data from 'users' with PK: {referral_owner}"
        )

    logging.info(f"Successfully updated user entry for {referral_owner}.")

    # Calls create_user to create a new UsersEntry object for the user who used the referral code
    await create_user(user)

    logging.info(f"Successfully created user {user}.")

    return JSONResponse(
        status_code=200,
        content={"detail": f"Successfully used referral code {code} for user {user}."},
    )


async def get_details_from_username(username: str):
    """
    Gets the details of a user from their username.
    """
    try:
        details = USERS_DAO.find_most_recent_by_pk(username)
    except ClientError as _:
        raise DatabaseLoadFailureException(
            message=f"Exception: Boto3 exception whilst fetching data from 'users' with PK: {username}"
        )
    except Exception as _:
        raise DatabaseLoadFailureException(
            message=f"Exception: Unknown exception whilst fetching data from 'users' with PK: {username}"
        )

    if details:
        return details
    else:
        return JSONResponse(
            status_code=400,
            content={"detail": f"User {username} does not exist."},
        )
    

async def get_username(request: Request):
    # First, fetches the access token from the request header
    try:
        token = request.headers.get("Authorization").strip("Bearer").strip()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "title": "Incorrect/Missing Access Token",
                "body": "The access token provided was incorrect or missing.",
            },
        )

    logging.info(f"{token}")

    # Then, calls get_user() to get the user who sent the request
    sender = get_username_from_access_token(token)

    logging.info(f"Sender: {sender}")

    if sender == {}:
        raise HTTPException(
            status_code=400,
            detail={
                "title": "Invalid Access Token",
                "body": "The access token provided was invalid.",
            },
        )

    return sender.get("username")


@router.get("/details", include_in_schema=True)
async def get_details(request: Request):
    # First, fetches the access token from the request header
    sender = await get_username(request)

    logging.info(sender)

    return await get_details_from_username(sender)


async def send_email_invite(email: str, referral_code: str):
    subject = f"You've Been Invited! {referral_code}"
    logging.info(f"Sending invite email to user {email}.")

    # TODO: Add the correct encoded URL to this email
    body = render_template(
        "referral-invite.html",
        title=subject,
        username=email,
        url="https://rug.ai",
    )

    email_subject = subject
    email_body = body

    try:
        _ = ses.send_email(
            Source="no-reply@rug.ai",
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {"Data": email_subject},
                "Body": {"Html": {"Data": email_body}},
            },
        )

        return True
    except Exception as e:
        logging.info(f"Exception: {e}")
        return False


@router.post("/invite", include_in_schema=True)
async def invite_user(request: Request, user: str):
    """
    Sends an email inviting a user to join the platform.

    Determines who the sender is by checking the header of the request for an Authorization token.

    Then asks Cognito who the sender is and uses this to determine the referral code to use. Then wraps this referral code into an email.
    """
    # Then, calls is_referral_exists() to get the referral code of the sender
    user_details = await get_details(request)

    referral_code = user_details.get("referral_code")
    sender = user_details.get("username")

    if not referral_code:
        raise HTTPException(
            status_code=400,
            detail=f"User {sender} does not have a referral code.",
        )

    logging.info(f"Referral code: {referral_code}")

    # Now formats the email to send to the user
    confirmed = await send_email_invite(user, referral_code)

    if confirmed:
        # TODO: Add the unconfirmed email to the list of unconfirmed emails in the database for the inviter

        return JSONResponse(
            status_code=200,
            content={"detail": f"Successfully invited user {user}."},
        )
    else:
        return JSONResponse(
            status_code=400,
            content={
                "detail": f"Failed to invite user {user} as we were unable to send the email invite."
            },
        )
