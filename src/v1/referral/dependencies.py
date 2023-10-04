import re, random

from src.v1.auth.exceptions import InvalidReferralCodeFormat, InvalidReferralCode

def generate_hex_string(length=6):
    # Generate a random hexadecimal string of the specified length
    return "".join(random.choice("0123456789abcdef") for _ in range(length))


def check_if_referral_code_exists(code: str):
    # TODO: Check if the referral code exists in the database
    return False


def generate_referral_code():
    code = generate_hex_string(length=6)

    success = False
    while not success:
        # Do requisite checks
        exists = check_if_referral_code_exists(code)
        if not exists:
            success = True
        else:
            code = generate_hex_string(length=6)
            continue

    return code
