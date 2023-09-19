import os
import boto3, logging
from fastapi import Depends, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

from src.v1.auth.schemas import (EmailAccountBase, CreateEmailAccount, 
SignInEmailAccount, VerifyEmailAccount,
UserAccessTokens, ResetPassword)

from src.v1.referral.endpoints import post_referral_code_use

router = APIRouter()

# Initialize Cognito client
cognito = boto3.client('cognito-idp', region_name="eu-west-2")

@router.post("/email/create/")
async def create_user(user: CreateEmailAccount):
    CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID")

    if not CLIENT_ID:
        # TODO: Add custom exception for this
        raise ValueError()

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
#         {
#   "detail": "An error occurred (UsernameExistsException) when calling the SignUp operation: An account with the given email already exists."
#           }
# TODO: Add handling for this exception
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # TODO: Post a referral code use for the code
    # NOTE: The code was validated by the input validation at the point of call
    try:
        post_referral_code_use(user.referral_code, user.username)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return JSONResponse(status_code=200, content={
            "detail": "User created successfully! Please verify your email using the link or code sent by AWS Cognito.",
        })


@router.post("/email/verify/")
async def verify_user(user: VerifyEmailAccount):
    CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID")

    if not CLIENT_ID:
        # TODO: Add custom exception for this
        raise ValueError()

    try:
        _ = cognito.confirm_sign_up(
            ClientId=CLIENT_ID,
            Username=user.username,
            ConfirmationCode=user.confirmation_code
        )

        # TODO: Add a users database insertion at this point

        return JSONResponse(status_code=200, content={"detail": "User account successfully verified!"})
    except cognito.exceptions.CodeMismatchException:
        raise HTTPException(status_code=400, detail="Invalid confirmation code.")
    except cognito.exceptions.ExpiredCodeException:
        raise HTTPException(status_code=400, detail="The confirmation code has expired.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/email/verify/resend")
async def resend_verification_code(user: EmailAccountBase):
    CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID")

    if not CLIENT_ID:
        # TODO: Add custom exception for this
        raise ValueError()

    try:
        _ = cognito.resend_confirmation_code(
            ClientId=CLIENT_ID,
            Username=user.username
        )
        # The new confirmation code will be sent to the user's registered email or phone number
        return JSONResponse(status_code=200, content={"message": "Confirmation code resent successfully."})
    except cognito.exceptions.UserNotFoundException:
        # TODO: Add exception handling here
        raise HTTPException(status_code=400, detail="User not found.")
    except cognito.exceptions.LimitExceededException:
        # TODO: Add exception handling here
        raise HTTPException(status_code=400, detail="Attempt limit exceeded, please try again later.")


@router.post("/email/signin/", response_model=UserAccessTokens)
async def sign_in(user: SignInEmailAccount):
    CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID")

    if not CLIENT_ID:
        # TODO: Add custom exception for this
        raise ValueError()

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
            "idToken": response.get('AuthenticationResult').get('IdToken'),
            "refreshToken": response.get('AuthenticationResult').get('RefreshToken'),
        }

        return UserAccessTokens(**tokens)
    except cognito.exceptions.NotAuthorizedException:
        # TODO: Raise a custom exception here for invalid authentication
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    except Exception as e:
        # TODO: Raise a catch-all exception here
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/email/password/request")
async def request_reset_password(user: EmailAccountBase):
    CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID")

    if not CLIENT_ID:
        raise ValueError()
    
    try:
        _ = cognito.forgot_password(
            ClientId=CLIENT_ID,
            Username=user
        )
        # The verification code will be sent to the user's registered email or phone number
        return JSONResponse(status_code=200, content={"detail": "Password reset code sent successfully."})
    except cognito.exceptions.UserNotFoundException:
        # TODO: Add exception handling here
        raise HTTPException(status_code=400, detail="User not found.")
    except cognito.exceptions.InvalidParameterException as e:
        # TODO: Add exception handling here
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/email/password/reset")
async def reset_password(user: ResetPassword):
    CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID")

    if not CLIENT_ID:
        raise ValueError()
    
    try:
        _ = cognito.confirm_forgot_password(
            ClientId=CLIENT_ID,
            Username=user.username,
            ConfirmationCode=user.verification_code,
            Password=user.new_password
        )
        # The user's password is now reset
        return JSONResponse(status_code=200, content={"detail": "Password reset successfully."})
    except cognito.exceptions.CodeMismatchException:
        # TODO: Add exception handling here
        raise HTTPException(status_code=400, detail="Invalid verification code.")
    except cognito.exceptions.ExpiredCodeException:
        # TODO: Add exception handling here
        raise HTTPException(status_code=400, detail="The verification code has expired.")
    except cognito.exceptions.UserNotFoundException:
        # TODO: Add exception handling here
        raise HTTPException(status_code=400, detail="User not found.")
    except cognito.exceptions.InvalidParameterException as e:
        # TODO: Add exception handling here
        raise HTTPException(status_code=400, detail=str(e))
