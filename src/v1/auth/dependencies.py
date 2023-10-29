import re, jinja2


def is_referral_format_valid(s):
    pattern = r"^[0-9a-fA-F]{6}$"
    return bool(re.match(pattern, s))


def render_template(template, **kwargs):
    templateLoader = jinja2.FileSystemLoader(searchpath="src/v1/auth/email/templates")
    templateEnv = jinja2.Environment(loader=templateLoader)
    templ = templateEnv.get_template(template)
    return templ.render(kwargs)
