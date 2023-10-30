import jinja2


def render_template(template, **kwargs):
    """renders a Jinja HTML template"""
    templateLoader = jinja2.FileSystemLoader(searchpath="src/v1/auth/email/templates")
    templateEnv = jinja2.Environment(loader=templateLoader)
    templ = templateEnv.get_template(template)
    return templ.render(kwargs)


if __name__ == "__main__":
    print(
        render_template(
            "referral-invite.html",
            title="You've Been Invited!",
            username="John",
            url="https://rug.ai",
        )
    )

    print(
        render_template(
            "otp.html",
            title="OTP",
            username="John",
            code="123 456",
            url="https://Rug.ai",
        )
    )

    print(
        render_template(
            "reset-password.html",
            title="You've Requested to Reset Your Password",
            username="RugEnjoyer",
            reset_link="https://rug.ai/reset-pwd?username=xxxxx&code=123456",
        )
    )

    print(
        render_template("join-waitlist.html", title="Thanks for Joining the Waitlist!")
    )

    print(
        render_template(
            "welcome.html",
            title="Welcome to Rug.ai",
            url="https://Rug.ai/signup?ref=123456",
        )
    )

    print(
        render_template(
            "airdrop.html",
            title="Your Weekly Airdrop",
            username="RugEnjoyer",
            total_points="284",
            points="24",
            points_direction="unchanged",  # up, down, unchanged
            rank="3,313",
            rank_out_of="50k",
            rank_delta="14",
            rank_direction="down",  # up, down, unchanged
            points_distributed="248",
            invites="36",
            total_users="157",
        )
    )

    print(
        render_template(
            "password-reset-successfully.html",
            title="You've Successfully Reset Your Password",
            username="RugEnjoyer",
            signin_link="https://rug.ai/signin",
        )
    )
