# from fastapi import APIRouter
# from fastapi.responses import JSONResponse
# from botocore.exceptions import ClientError
# import logging, time

# from src.v1.referral.dependencies import generate_referral_code, check_if_referral_code_exists
# from src.v1.referral.exceptions import UserDoesNotExist
# from src.v1.referral.schemas import UserReferralData, ReferralCode, ReferralCodeUse
# from src.v1.referral.constants import EXPIRY_BUFFER, DEFAULT_NUMBER_OF_USES

# from src.v1.shared.DAO import DAO
# from src.v1.shared.exceptions import DatabaseLoadFailureException

# REFERRAL_CODE_DAO = DAO('referralcodes')

# router = APIRouter()

# @router.get("/current/{user}", response_model=UserReferralData, include_in_schema=True)
# async def get_referral_code(user: str):
#     """
#     Gets the referral code for the user, if it exists.
#     """
#     try:
#         user_data = USERS_DAO.find_most_recent_by_pk(user)
#     except ClientError as _:
#         raise DatabaseLoadFailureException(message=f"Exception: Boto3 exception whilst fetching data from 'users' with PK: {user}")
#     except Exception as _:
#         raise DatabaseLoadFailureException(message=f"Exception: Unknown exception whilst fetching data from 'users' with PK: {user}")
    
#     if user_data:
#         return UserReferralData(**user_data)
#     else:
#         raise UserDoesNotExist(user, f"Exception: User with username {user} does not exist in the database.")


# @router.post("/generate/{user}", response_model=ReferralCode, include_in_schema=True)
# async def generate_referral_code(user: str):
#     """
#     Generates a new referral code for the user and updates the metadata in the database.

#     If the user does not have a referral code, this will create the first code for the user.

#     Otherwise, it will generate a new code, increment all data accordingly and update the database.
#     """
#     try:
#         existing_referral_code = get_referral_code(user)
#     except UserDoesNotExist as _:
#         logging.warning(f"Exception: User with username {user} does not exist in the database. Proceeding to generate a new referral code for the user.")
#         existing_referral_code = None

#     current_referral_code = existing_referral_code.get('referralCode') if existing_referral_code else None

#     if not current_referral_code:
#         # Generate a new referral code with a default number of uses
#         new_referral_code = ReferralCode(
#                                 code=generate_referral_code(), 
#                                 expiry=int(time.time()) + EXPIRY_BUFFER, 
#                                 initialUses=DEFAULT_NUMBER_OF_USES,
#                                 uses=[]
#                                 )
#     else:
#         # Generate a new referral code with the number of uses from the previous code
#         referral_code_details = get_referral_code_details(current_referral_code)
#         number_of_uses = referral_code_details.get('numberOfUses')

#         if number_of_uses == 0:
#             raise Exception(f"Exception: The referral code {current_referral_code} has no uses remaining.")
        
#         new_referral_code = ReferralCode(
#                                 code=generate_referral_code(), 
#                                 expiry=int(time.time()) + EXPIRY_BUFFER, 
#                                 initialUses=number_of_uses,
#                                 uses=[]
#                                 )
    
#     # TODO: Update the database for the user with this new referral code object
#     # TODO: Update the database for the referral code with the new referral code object

#     return new_referral_code

# @router.get("/details/{code}", response_model=ReferralCode, include_in_schema=True)
# async def get_referral_code_details(code: str):
#     """
#     Fetches details on the most up-to-date referral code for the user, including how many invites are left.
#     """
#     try:
#         referral_code_data = REFERRAL_CODE_DAO.find_most_recent_by_pk(code)
#     except ClientError as e:
#         raise DatabaseLoadFailureException(message=f"Exception: Boto3 exception whilst fetching data from 'referralcodes' with PK: {code}")
    
#     if referral_code_data:
#         return ReferralCode(**referral_code_data)
#     else:
#         # TODO: Write custom exception to handle this case
#         raise Exception(f"Exception: Referral code {code} does not exist in the database.")


# # TODO: Add check that `user` exists in the database
# @router.post("/use/{code}", include_in_schema=True)
# async def post_referral_code_use(code: str, user: str):
#     """
#     Increments the number of uses for the referral code and updates the database.
#     """
#     try:
#         referral_code_details = get_referral_code_details(code)
#     except Exception as e:
#         raise e
    
#     number_of_uses = referral_code_details.get('numberOfUses')

#     if number_of_uses == 0:
#         raise Exception(f"Exception: The referral code {code} has no uses remaining.")
#     elif referral_code_details.get('expiry') < int(time.time()):
#         raise Exception(f"Exception: The referral code {code} has expired.")

#     referral_code_use = ReferralCodeUse(username=user, timestamp=int(time.time()))

#     updated_referral_code = ReferralCode(
#                                 code=code,
#                                 expiry=referral_code_details.get('expiry'),
#                                 initialUses=referral_code_details.get('initialUses'),
#                                 uses=referral_code_details.get('uses').append(referral_code_use)
#                                 )
    
#     # TODO: Update the database for the referral code with the new referral code object

#     return JSONResponse(status_code=200, content={"detail": f"Successfully used referral code {code} for user {user}."})


# @router.get("/stats/{user}", include_in_schema=True)
# async def get_user_stats(user: str):
#     """
#     Fetches details on the user invite statistics for a given user, including the number of points earned.
#     """
#     user_data = get_referral_code(user)

#     referral_codes = user_data.get('previousReferralCodes').append(user_data.get('referralCode'))

#     referral_details = [await get_referral_code_details(code) for code in referral_codes]

#     total_referrals = sum([referral.numberUses for referral in referral_details])

#     # TODO: Add handling for second order referrals, such as when a user refers a user who refers a user

#     return JSONResponse(status_code=200, content={"detail": total_referrals})


# def post_email_invite(user: str, email: str):
#     """
#     Sends an email invite to the given email address.
#     """
#     return


# def get_invite_history(user: str):
#     """
#     Fetches the invite history for a given user.
#     """
#     return


# def get_invite_chart(user: str):
#     """
#     Fetches the invite chart for a given user.
#     """
#     return
