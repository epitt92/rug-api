# import logging

# class InvalidReferralCode(ValueError):
#     """
#     Raised when the referral code is invalid based on a check in the database.
#     For example, if the user has no more available invites.
#     """
#     def __init__(self, code: str, message: str):
#         logging.error(message)
#         self.message = message
#         super().__init__(self.message)


# class InvalidReferralCodeFormat(ValueError):
#     """
#     Raised when the referral code is invalid based on a formatting check.
#     This will be because the code provided was not a hexadecimal string of length 6.
#     """
#     def __init__(self, code: str, message: str):
#         logging.error(message)
#         self.message = message
#         super().__init__(self.message)


# class IncorrectCredentials(ValueError):
#     """
#     Raised when the user provides incorrect credentials to sign into the service.
#     """
#     def __init__(self, username: str, password: str, message: str):
#         self.message = message
#         super().__init__(self.message)


# class UserDoesNotExist(Exception):
#     """
#     Raised when the user, given by their username, does not exist in the database.
#     """
#     def __init__(self, username: str, message: str):
#         self.message = message
#         super().__init__(self.message)
