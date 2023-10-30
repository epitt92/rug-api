import re, jinja2, boto3, logging

cognito = boto3.client("cognito-idp", region_name="eu-west-2")


def is_referral_format_valid(s):
    pattern = r"^[0-9a-fA-F]{6}$"
    return bool(re.match(pattern, s))


def render_template(template, **kwargs):
    templateLoader = jinja2.FileSystemLoader(searchpath="src/v1/auth/email/templates")
    templateEnv = jinja2.Environment(loader=templateLoader)
    templ = templateEnv.get_template(template)
    return templ.render(kwargs)


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
