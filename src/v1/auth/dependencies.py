import re, jinja2

from src.v1.auth.exceptions import InvalidReferralCodeFormat, InvalidReferralCode


def is_referral_format_valid(s):
    pattern = r"^[0-9a-fA-F]{6}$"
    return bool(re.match(pattern, s))


def validate_referral_code(code: str):
    is_code_format_valid = is_referral_format_valid(code)

    if not is_code_format_valid:
        raise InvalidReferralCodeFormat(
            code,
            f"Exception: Invalid referral code format, the provided code {code} is not a hexadecimal string of length 6.",
        )

    # TODO: Check if the referral code exists in the database
    is_valid_referral = True

    if not is_valid_referral:
        raise InvalidReferralCode(
            code,
            f"Exception: Invalid referral code, the provided code {code} is not valid.",
        )

    return code


def render_template(template, **kwargs):
    templateLoader = jinja2.FileSystemLoader(searchpath="src/v1/auth/email/templates")
    templateEnv = jinja2.Environment(loader=templateLoader)
    templ = templateEnv.get_template(template)
    return templ.render(kwargs)
