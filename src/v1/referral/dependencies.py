# import re, random, boto3

# from src.v1.shared.DAO import DAO

# from src.v1.auth.exceptions import InvalidReferralCodeFormat, InvalidReferralCode

# # DynamoDB setup
# # TODO: Refactor this into a DAO object
# dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
# table = dynamodb.Table('referralcodes')

# def generate_hex_string(length=6):
#     # Generate a random hexadecimal string of the specified length
#     return "".join(random.choice("0123456789abcdef") for _ in range(length))


# def check_if_referral_code_exists(code: str):
#     # Check if the referral code is valid
#     response = table.scan(
#         FilterExpression="referral_code = :referral_code_val",
#         ExpressionAttributeValues={":referral_code_val": code}
#     )

#     if 'Items' not in response or not response['Items']:
#         raise True

#     return False


# def generate_referral_code():
#     code = generate_hex_string(length=6)

#     success = False
#     while not success:
#         # Do requisite checks
#         exists = check_if_referral_code_exists(code)
#         if not exists:
#             success = True
#         else:
#             code = generate_hex_string(length=6)
#             continue

#     return code
