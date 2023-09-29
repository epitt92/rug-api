import os
import boto3, logging
from fastapi import Depends, HTTPException, APIRouter, Response
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel, EmailStr
from botocore.exceptions import ClientError

from src.v1.auth.schemas import (
        EmailAccountBase, CreateEmailAccount, 
        SignInEmailAccount, VerifyEmailAccount,
        UserAccessTokens, ResetPassword, 
        CreateWeb3Account, SignInWeb3Account)

from src.v1.referral.endpoints import post_referral_code_use

from src.v1.auth.exceptions import CognitoException, CognitoUserAlreadyExists, CognitoIncorrectCredentials, CognitoLambdaException, CognitoUserDoesNotExist

router = APIRouter()

# Initialize Cognito client
cognito = boto3.client('cognito-idp', region_name="eu-west-2")

##############################################
#                                            #
#             Authorize JWT                  #
#                                            #
##############################################

class Settings:
    JWT_SECRET = ""
    JWT_ALGORITHM = "RS256"

@AuthJWT.load_config
def get_config():
    return Settings()

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
            except Exception as e:
                logging.error(f"Exception: An exception occurred whilst attempting to rollback user creation: {e}")

            raise CognitoUserAlreadyExists(user.username, f"User with given email {user.username} already exists.")
        elif error_code == "UnexpectedLambdaException":
            try:
                await rollback_user_creation(user.username)
            except Exception as e:
                logging.error(f"Exception: An exception occurred whilst attempting to rollback user creation: {e}")

            raise CognitoLambdaException(f"Exception: UnexpectedLambdaException: {e}")
        else:
            try:
                await rollback_user_creation(user.username)
            except Exception as e:
                logging.error(f"Exception: An exception occurred whilst attempting to rollback user creation: {e}")

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
async def sign_in(user: SignInEmailAccount, Authorize: AuthJWT = Depends()) -> Response:
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

        # Set the tokens as cookies in the response
        # httponly=True prevents the cookie from being accessed by JavaScript, which prevents cross-site scripting attacks
        # secure=True ensures that the cookie is only sent over HTTPS

        # response.set_cookie(key="accessToken", value=tokens.get('accessToken'), httponly=True, secure=True)
        # response.set_cookie(key="refreshToken", value=tokens.get('refreshToken'), httponly=True, secure=True)

        # Authorize.set_access_cookies(tokens.get('accessToken'))
        # Authorize.set_refresh_cookies(tokens.get('refreshToken'))
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


@router.post("/email/password/request")
async def request_reset_password(user: EmailAccountBase):
    CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID")

    if not CLIENT_ID:
        raise CognitoException("Exception: COGNITO_APP_CLIENT_ID not set in environment variables.")
    
    try:
        # The verification code will be sent to the user's registered email or phone number
        _ = cognito.forgot_password(
            ClientId=CLIENT_ID,
            Username=user.username
        )
    except cognito.exceptions.UserNotFoundException as e:
        raise CognitoUserDoesNotExist(user, f"Exception: UserNotFoundException: {e}")
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


@router.post("/web3/signup/")
async def sign_up_web3(user: CreateWeb3Account):
    pass


@router.post("/web3/signin", response_model=UserAccessTokens)
async def sign_in_web3(user: SignInWeb3Account):
    pass
