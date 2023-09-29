import jinja2

#########################################
#                                       #
#           Email Templates             #
#                                       #
#########################################

def render_template(template, **kwargs):
    templateLoader = jinja2.FileSystemLoader(searchpath="./templates")
    templateEnv = jinja2.Environment(loader=templateLoader)
    templ = templateEnv.get_template(template)
    return templ.render(kwargs)

#########################################
#                                       #
#        Lambda Event Handlers          #
#                                       #
#########################################

def custom_message_sign_up(event):
    verification_code = event['request']['codeParameter']

    subject = "Your One-Time Passcode"
    body = render_template('otp.html', code=verification_code, url="https://rug.ai")

    event['response']['emailSubject'] = subject
    event['response']['emailMessage'] = body

    return event


def custom_message_resend_code(event):
    return event


def custom_message_forgot_password(event):
    return event


def post_authentication(event):
    return event


def post_password_change(event):

    return event


def lambda_handler(event, context):
    if event['triggerSource'] == 'CustomMessage_SignUp':
        return custom_message_sign_up(event)
    elif event['triggerSource'] == 'CustomMessage_ResendCode':
        return custom_message_resend_code(event)
    elif event['triggerSource'] == 'CustomMessage_ForgotPassword':
        return custom_message_forgot_password(event)
    elif event['triggerSource'] == 'PostAuthentication_Authentication':
        return post_authentication(event)
    elif event['triggerSource'] == 'PostPasswordChange_PasswordChange':
        return post_password_change(event)
    else:
        return event
