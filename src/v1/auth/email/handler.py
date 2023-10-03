import jinja2
import boto3

ses = boto3.client('ses', region_name="eu-west-2")

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

    subject = "You've Requested to Reset Your Password"
    reset_link = f"https://rug.ai/reset-pwd?username={recipient}&code={reset_code}"
    body = render_template('reset-password.html', title=subject, username=recipient, reset_link=reset_link)

    event['response']['emailSubject'] = subject
    event['response']['emailMessage'] = body
    return event


def send_custom_message_confirm_password_reset(event):
    recipient = event['request']['userAttributes']['email']

    subject = "You've Successfully Reset Your Password"
    body = render_template('password-reset-successfully.html', title=subject, username=recipient, signin_link="https://rug.ai/signin")

    email_subject = subject
    email_body = body

    ses.send_email(
        Source="no-reply@rug.ai",
        Destination={
            'ToAddresses': [
                recipient
            ]
        },
        Message={
            'Subject': {
                'Data': email_subject
            },
            'Body': {
                'Html': {
                    'Data': email_body
                }
            }
        }
    )

    return


def lambda_handler(event, context):
    if event['triggerSource'] == 'CustomMessage_SignUp':
        return custom_message_sign_up(event)
    elif event['triggerSource'] == 'CustomMessage_ResendCode':
        return custom_message_sign_up(event)
    elif event['triggerSource'] == 'CustomMessage_ForgotPassword':
        return custom_message_forgot_password(event)
    elif event['triggerSource'] == 'PostConfirmation_ConfirmForgotPassword':
        # This trigger does not have email functionality by default
        send_custom_message_confirm_password_reset(event)
        return event
    # elif event['triggerSource'] == 'PostAuthentication_Authentication':
    #     return post_authentication(event)
    # elif event['triggerSource'] == 'PostPasswordChange_PasswordChange':
    #     return post_password_change(event)
    else:
        return event
