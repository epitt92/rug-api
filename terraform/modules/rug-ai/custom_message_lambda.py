import json

def lambda_handler(event, context):
    if event['triggerSource'] == 'CustomMessage_SignUp':
        event['response']['emailSubject'] = 'Welcome to Our Platform!'
        event['response']['emailMessage'] = """
        <html>
        <body>
        <p>Thank you for signing up with us!</p>
        <p>Your verification code is <strong>{####}</strong>. Use this code to complete your registration.</p>
        </body>
        </html>
        """
    return event