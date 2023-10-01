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


def custom_message_forgot_password(event):
    recipient = event['request']['userAttributes']['email']
    reset_code = event['request']['codeParameter']

    # TODO: Must incorporate the reset code into the link
    subject = "You've Requested to Reset Your Password"
    body = render_template('reset-password.html', title=subject + f": {reset_code}", username=recipient, reset_link="https://rug.ai")

    event['response']['emailSubject'] = subject
    event['response']['emailMessage'] = body
    return event


def lambda_handler(event, context):
    if event['triggerSource'] == 'CustomMessage_SignUp':
        return custom_message_sign_up(event)
    elif event['triggerSource'] == 'CustomMessage_ResendCode':
        return custom_message_sign_up(event)
    elif event['triggerSource'] == 'CustomMessage_ForgotPassword':
        return custom_message_forgot_password(event)
    # elif event['triggerSource'] == 'PostAuthentication_Authentication':
    #     return post_authentication(event)
    # elif event['triggerSource'] == 'PostPasswordChange_PasswordChange':
    #     return post_password_change(event)
    else:
        return event
