import os, boto3, logging, requests, time
from functools import lru_cache
from fastapi import Depends, HTTPException, APIRouter, Response, security
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel, EmailStr
from botocore.exceptions import ClientError
from authlib.jose import JsonWebToken, JsonWebKey, KeySet, JWTClaims, errors
from cachetools import cached, TTLCache

from src.v1.referral.endpoints import post_referral_code_use
from src.v1.shared.DAO import DAO

from src.v1.auth.exceptions import CognitoException, CognitoUserAlreadyExists, CognitoIncorrectCredentials, CognitoLambdaException, CognitoUserDoesNotExist
from src.v1.auth.dependencies import render_template
from src.v1.auth.schemas import (
        EmailAccountBase, CreateEmailAccount,
        SignInEmailAccount, VerifyEmailAccount,
        UserAccessTokens, ResetPassword)

router = APIRouter()

token_scheme = security.HTTPBearer()

# Initialize Cognito client
cognito = boto3.client('cognito-idp', region_name="eu-west-2")
ses = boto3.client('ses', region_name="eu-west-2")

WHITELIST_DAO = DAO(table_name='whitelist')

##############################################
#                                            #
#             Authorize JWT                  #
#                                            #
##############################################

class Settings(BaseModel):
    JWT_SECRET = "secret"
    JWT_ALGORITHM = "RS256"

    cognito_user_pool_id: str = os.environ.get('COGNITO_USER_POOL_ID')

@lru_cache()
def get_settings() -> Settings:
    """
    Load settings (once per app lifetime)
    """
    return Settings()

def get_jwks_url(settings: Settings = Depends(get_settings)) -> str:
    """
    Build JWKS url
    """
    pool_id = settings.cognito_user_pool_id
    region = pool_id.split("_")[0]
    return f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json"

@cached(TTLCache(maxsize=1, ttl=3600))
def get_jwks(url: str = Depends(get_jwks_url)) -> KeySet:
    """
    Get cached or new JWKS. Cognito does not seem to rotate keys, however to be safe we
    are lazy-loading new credentials every hour.
    """
    with requests.get(url) as response:
        response.raise_for_status()
        return JsonWebKey.import_key_set(response.json())

def decode_token(
    token: security.HTTPAuthorizationCredentials = Depends(token_scheme),
    jwks: KeySet = Depends(get_jwks),
) -> JWTClaims:
    """
    Validate & decode JWT.
    """
    try:
        claims = JsonWebToken(["RS256"]).decode(
            s=token.credentials,
            key=jwks,
            #  claim_options={
                # Example of validating audience to match expected value
                # "aud": {"essential": True, "values": [APP_CLIENT_ID]}
            #  }
        )

        if "client_id" in claims:
            # Insert Cognito's `client_id` into `aud` claim if `aud` claim is unset
            claims.setdefault("aud", claims["client_id"])

        claims.validate()
    except errors.JoseError:
        raise HTTPException(status_code=403, detail="Bad auth token")

    return claims

##############################################
#                                            #
#          JWT Token Validation              #
#                                            #
##############################################

@router.get("/email/validate/")
def validate_access_token(access_token: str) -> bool:
    try:
        response = cognito.get_user(AccessToken=access_token)
        return access_token if response.get("Username") else False
    except cognito.exceptions.NotAuthorizedException as e:
        logging.error(f"Exception: NotAuthorizedException: {e}")
        return False
    except Exception as e:
        logging.error(f"Exception: Unknown Cognito Exception: {e}")
        return False

@router.get("/email/username/")
def get_username_from_access_token(access_token: str) -> str:
    try:
        response = cognito.get_user(AccessToken=access_token)
        logging.info(f"Response: {response}")
        user_attributes = response.get("UserAttributes")

        if user_attributes:
            for attribute in user_attributes:
                if attribute.get("Name") == "email":
                    return {"username": attribute.get("Value")}
        logging.error(f"Exception: No email attribute found in response: {response}")
        return {}
    except cognito.exceptions.NotAuthorizedException as e:
        logging.error(f"Exception: NotAuthorizedException: {e}")
        return {}
    except Exception as e:
        logging.error(f"Exception: Unknown Cognito Exception: {e}")
        return {}


@router.get("/email/refresh/")
def refresh_access_token(refresh_token: str) -> Response:
    CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID")

    if not CLIENT_ID:
        # TODO: Add custom exception for this
        raise CognitoException("Exception: COGNITO_APP_CLIENT_ID not set in environment variables.")

    try:
        response = cognito.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': refresh_token
            }
        )

        if response.get('AuthenticationResult'):
            access_token = response.get('AuthenticationResult').get('AccessToken')
            return JSONResponse(status_code=200, content={"accessToken": access_token})
        else:
            return None
    except ClientError as e:
        logging.warning(f"Exception: ClientError whilst attempting to refresh access token: {e}")
        return None
    

@router.get("/email/exists/") 
async def check_username_exists(user: EmailStr):
    USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID")

    if not USER_POOL_ID:
        raise CognitoException("Exception: COGNITO_USER_POOL_ID not set in environment variables.")

    try:
        response = cognito.admin_get_user(
            UserPoolId=USER_POOL_ID,
            Username=user
        )
        if response and 'Username' in response:
            return JSONResponse(status_code=200, content={"exists": True, "detail": "Username already exists."})
        else:
            return JSONResponse(status_code=200, content={"exists": False, "detail": "Username is available."})
    except cognito.exceptions.UserNotFoundException:
        return JSONResponse(status_code=200, content={"exists": False, "detail": "Username is available."})
    except Exception as e:
        raise CognitoException(str(e))


@router.delete("/email/delete/")
async def rollback_user_creation(access_token: str = Depends(validate_access_token)) -> Response:
    USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID")

    if not USER_POOL_ID:
        raise CognitoException("Exception: COGNITO_USER_POOL_ID not set in environment variables.")

    # Rollback: Delete the user from Cognito if an error occurred after sign_up
    try:
        username = get_username_from_access_token(access_token).get("username")

        if not username:
            raise CognitoException("Exception: No username found in access token.")

        cognito.admin_delete_user(
            UserPoolId=USER_POOL_ID,  # Replace with your User Pool ID
            Username=username
        )
    except ClientError as e:
        logging.error(f"Exception: ClientError whilst attempting to rollback user creation: {e}")
        raise CognitoException(f"Exception: ClientError whilst attempting to rollback user creation: {e}")

    return JSONResponse(status_code=200, content={"detail": f"User {username} successfully rolled back and deleted from Cognito."})

##############################################
#                                            #
#                Endpoints                   #
#                                            #
##############################################

@router.post("/email/create/")
async def create_user(user: CreateEmailAccount):
    CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID")

    if not CLIENT_ID:
        # TODO: Add custom exception for this
        raise CognitoException("Exception: COGNITO_APP_CLIENT_ID not set in environment variables.")

    logging.info(f"Client ID: {CLIENT_ID}")

    try:
        _ = cognito.sign_up(
            ClientId=CLIENT_ID,
            Username=user.username,
            Password=user.password,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': user.username
                }
            ]
        )
    except ClientError as e:
        error_code = e.response['Error']['Code']

        logging.error(f"Exception: Boto3 ClientError thrown during call to `sign_up`: {e}")
        logging.error(f"Rolling back user creation for user {user.username}.")

        if error_code == "UsernameExistsException":
            try:
                await rollback_user_creation(user.username)
            except Exception as f:
                logging.error(f"Exception: An exception occurred whilst attempting to rollback user creation: {f}")

            raise CognitoUserAlreadyExists(user.username, f"User with given email {user.username} already exists.")
        elif error_code == "UnexpectedLambdaException":
            try:
                await rollback_user_creation(user.username)
            except Exception as f:
                logging.error(f"Exception: An exception occurred whilst attempting to rollback user creation: {f}")

            raise CognitoLambdaException(f"Exception: UnexpectedLambdaException: {e}")
        else:
            try:
                await rollback_user_creation(user.username)
            except Exception as f:
                logging.error(f"Exception: An exception occurred whilst attempting to rollback user creation: {f}")

            raise CognitoException(f"Exception: Unknown ClientError: {e}")
    except Exception as e:
        try:
            await rollback_user_creation(user.username)
        except Exception as e:
            logging.error(f"Exception: An exception occurred whilst attempting to rollback user creation: {e}")

        raise CognitoException(f"Exception: Unknown Cognito Exception: {e}")

    # Post a use on the referral code if this was successful
    # await post_referral_code_use(user.referral_code, user.username)

    return JSONResponse(status_code=200, content={"detail": "User created successfully! Please verify your email using the link or code sent by AWS Cognito.",})


@router.post("/email/verify/")
async def verify_user(user: VerifyEmailAccount):
    CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID")

    if not CLIENT_ID:
        # TODO: Add custom exception for this
        raise CognitoException("Exception: COGNITO_APP_CLIENT_ID not set in environment variables.")

    try:
        _ = cognito.confirm_sign_up(
            ClientId=CLIENT_ID,
            Username=user.username,
            ConfirmationCode=user.confirmation_code
        )

        # TODO: Add a users database insertion at this point
    except cognito.exceptions.CodeMismatchException as e:
        raise HTTPException(status_code=400, detail="Invalid confirmation code.")
    except cognito.exceptions.ExpiredCodeException as e:
        raise HTTPException(status_code=400, detail="The confirmation code has expired.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return JSONResponse(status_code=200, content={"detail": "User account successfully verified!"})


@router.post("/email/verify/resend")
async def resend_verification_code(user: EmailAccountBase):
    CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID")

    if not CLIENT_ID:
        # TODO: Add custom exception for this
        raise ValueError()

    try:
        # The new confirmation code will be sent to the user's registered email or phone number
        _ = cognito.resend_confirmation_code(
            ClientId=CLIENT_ID,
            Username=user.username
        )
    except cognito.exceptions.UserNotFoundException as e:
        # TODO: Add exception handling here
        raise CognitoUserDoesNotExist(user.username, f"Exception: UserNotFoundException for user {user.username}")
    except cognito.exceptions.LimitExceededException as e:
        # TODO: Add exception handling here
        raise CognitoException(f"Exception: LimitExceededException for user {user.username}")
    except Exception as e:
        raise CognitoException(f"Exception: Unknown Cognito Exception for user {user.username}")

    return JSONResponse(status_code=200, content={"message": "Confirmation code resent successfully."})


@router.post("/email/signin/", response_model=UserAccessTokens)
async def sign_in(user: SignInEmailAccount) -> Response:
    CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID")

    if not CLIENT_ID:
        # TODO: Add custom exception for this
        raise CognitoException("Exception: COGNITO_APP_CLIENT_ID not set in environment variables.")

    try:
        response = cognito.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': user.username,
                'PASSWORD': user.password
            }
        )

        # Return the JWT tokens
        tokens = {
            "accessToken": response.get('AuthenticationResult').get('AccessToken'),
            "refreshToken": response.get('AuthenticationResult').get('RefreshToken'),
        }
    except cognito.exceptions.NotAuthorizedException as e:
        # Raise a custom exception here for invalid authentication
        raise CognitoIncorrectCredentials(user.username, user.password, f"Exception: NotAuthorizedException for user {user.username}")
    except ClientError as e:
        error_code = e.response['Error']['Code']

        logging.error(f"Exception: Boto3 ClientError thrown during call to `sign_in`: {e}")
        logging.error(f"Username: {user.username} Password: {user.password}")

        raise CognitoException(f"Exception: Unknown ClientError with Error Code {error_code}: {e}")
    except Exception as e:
        # TODO: Raise a catch-all exception here
        raise CognitoException(f"Exception: Unknown Cognito Exception: {e}")

    return UserAccessTokens(**tokens)


@router.post("/email/refresh")
async def refresh(Authorize: AuthJWT = Depends()):
    Authorize.jwt_refresh_token_required()

    current_user = Authorize.get_jwt_subject()
    new_access_token = Authorize.create_access_token(subject=current_user)

    Authorize.set_access_cookies(new_access_token)
    return {"access_token": new_access_token}


@router.delete("/email/signout")
async def sign_out(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    Authorize.unset_jwt_cookies()
    return JSONResponse(status_code=200, content={"detail": "User successfully signed out."})


@router.post("/email/password/request")
async def request_reset_password(username: EmailStr):
    CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID")

    if not CLIENT_ID:
        raise CognitoException("Exception: COGNITO_APP_CLIENT_ID not set in environment variables.")

    try:
        # The verification code will be sent to the user's registered email or phone number
        _ = cognito.forgot_password(
            ClientId=CLIENT_ID,
            Username=username
        )
    except cognito.exceptions.UserNotFoundException as e:
        raise CognitoUserDoesNotExist(username, f"Exception: UserNotFoundException: {e}")
    except cognito.exceptions.InvalidParameterException as e:
        raise CognitoException(f"Exception: InvalidParameterException: {e}")
    except Exception as e:
        raise CognitoException(f"Exception: Unknown Cognito Exception: {e}")

    return JSONResponse(status_code=200, content={"detail": "Password reset code sent successfully."})


@router.post("/email/password/reset")
async def reset_password(user: ResetPassword):
    CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID")

    if not CLIENT_ID:
        raise CognitoException("Exception: COGNITO_APP_CLIENT_ID not set in environment variables.")

    try:
        _ = cognito.confirm_forgot_password(
            ClientId=CLIENT_ID,
            Username=user.username,
            ConfirmationCode=user.verification_code,
            Password=user.new_password
        )
        # The user's password is now reset
        return JSONResponse(status_code=200, content={"detail": "Password reset successfully."})
    except cognito.exceptions.CodeMismatchException as e:
        # TODO: Add exception handling here
        raise HTTPException(status_code=400, detail="Invalid verification code.")
    except cognito.exceptions.ExpiredCodeException as e:
        # TODO: Add exception handling here
        raise HTTPException(status_code=400, detail="The verification code has expired.")
    except cognito.exceptions.UserNotFoundException as e:
        # TODO: Add exception handling here
        raise HTTPException(status_code=400, detail="User not found.")
    except cognito.exceptions.InvalidParameterException as e:
        # TODO: Add exception handling here
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def send_confirmation_join_waitlist(email: str):
    subject = "Thanks for Joining the rug.ai Waitlist!"
    body = render_template('join-waitlist.html', title=subject)

    email_subject = subject
    email_body = body
    
    try:
        ses.send_email(
            Source="no-reply@rug.ai",
            Destination={
                'ToAddresses': [
                    email
                ]
            },
            Message={
                'Subject': {
                    'Data': email_subject
                },
                'Body': {
                    'Html': {
                        'Data': email_body
                    }
                }
            }
        )

        return True
    except Exception as e:
        logging.info(f"Exception: {e}")
        return False


@router.post("/waitlist")
async def join_waitlist(email: EmailStr):
    sign_up_time = int(time.time())

    waitlist_payload = {
        "timestamp": sign_up_time
    }

    sent = None
    
    try:
        WHITELIST_DAO.insert_one(email, item=waitlist_payload)

        # Send confirmation email to user
        sent = send_confirmation_join_waitlist(email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to insert user {email} into waitlist database.")

    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send confirmation email to user.")

    return JSONResponse(status_code=200, content={"detail": "Successfully joined waitlist."})
