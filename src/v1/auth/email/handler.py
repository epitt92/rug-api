import json, boto3, jinja2

ses = boto3.client('ses')

#########################################
#                                       #
#           Email Templates             #
#                                       #
#########################################

def render_template(template, **kwargs):
    templateLoader = jinja2.FileSystemLoader(searchpath="src/v1/auth/email/templates")
    templateEnv = jinja2.Environment(loader=templateLoader)
    templ = templateEnv.get_template(template)
    return templ.render(kwargs)

#########################################
#                                       #
#        Lambda Event Handler           #
#                                       #
#########################################

def lambda_handler(event, context):
    if event['triggerSource'] == 'CustomMessage_SignUp':
        recipient = event['request']['userAttributes']['email']
        username = event['username']
        verification_code = event['request']['codeParameter']

        subject = "Your One-Time Passcode"
        body = render_template('otp.html', username=username, code=verification_code, url="https://rug.ai")

        _ = ses.send_email(
            Source="no-reply@rug.ai",
            Destination={
                'ToAddresses': [
                    recipient,
                ]
            },
            Message={
                'Subject': {
                    'Data': subject
                },
                'Body': {
                    'Html': {
                        'Data': body
                    }
                }
            })

        event['response']['emailSubject'] = subject
        event['response']['emailMessage'] = body

    return event