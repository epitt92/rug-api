class InvalidReferralCodeFormat(ValueError):
    """
    Raised when the referral code is invalid based on a formatting check.
    This will be because the code provided was not a hexadecimal string of length 6.
    """

    def __init__(self, code: str, message: str):
        super().__init__(code, message)
