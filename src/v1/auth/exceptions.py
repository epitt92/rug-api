import logging

##########################################
#                                        #
#        Referral Code Exceptions        #
#                                        #
##########################################

class InvalidReferralCode(ValueError):
    """
    Raised when the referral code is invalid based on a check in the database.
    For example, if the user has no more available invites.
    """
    def __init__(self, code: str, message: str):
        logging.error(message)
        self.message = message
        super().__init__(self.message)


class InvalidReferralCodeFormat(ValueError):
    """
    Raised when the referral code is invalid based on a formatting check.
    This will be because the code provided was not a hexadecimal string of length 6.
    """
    def __init__(self, code: str, message: str):
        logging.error(message)
        self.message = message
        super().__init__(self.message)

##########################################
#                                        #
#           Cognito Exceptions           #
#                                        #
##########################################

class CognitoException(Exception):
    """
    Raised when the AWS Cognito service fails.
    """
    def __init__(self, message: str):
        logging.error(f"Exception: Root CognitoException Thrown: {message}")
        self.message = message
        super().__init__(self.message)

class CognitoUserAlreadyExists(CognitoException):
    """
    Raised when the user, given by their username, already exists in the database.
    """
    def __init__(self, username: str, message: str):
        logging.error(f"Exception: UserAlreadyExists in Cognito: {username}")
        self.message = message
        super().__init__(self.message)

class CognitoLambdaException(CognitoException):
    """
    Raised when the AWS Lambda function for Cognito fails.
    """
    def __init__(self, message: str):
        logging.error(f"Exception: CognitoLambdaException: {message}")
        self.message = message
        super().__init__(self.message)

class CognitoIncorrectCredentials(CognitoException):
    """
    Raised when the user provides incorrect credentials to sign into the service.
    """
    def __init__(self, username: str, password: str, message: str):
        logging.error(f"Exception: IncorrectCredentials in Cognito: {username} {password}")
        self.message = message
        super().__init__(self.message)

class CognitoUserDoesNotExist(CognitoException):
    """
    Raised when the user, given by their username, does not exist in the database.
    """
    def __init__(self, username: str, message: str):
        self.message = message
        super().__init__(self.message)
