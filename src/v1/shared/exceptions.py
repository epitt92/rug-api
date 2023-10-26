import logging


class RugAPIException(Exception):
    """
    Raised when an endpoint on another rug.ai API is called whose response fails.
    """

    def __init__(
        self,
        message: str = "An exception occurred while calling an external rug.ai endpoint.",
    ):
        logging.error(f"{message}")
        super().__init__(message)


class RPCProviderException(Exception):
    """
    Raised when an endpoint on a RPC provider is called whose response fails.
    """

    def __init__(
        self,
        message: str = "An exception occurred while calling an external RPC provider endpoint.",
    ):
        logging.error(f"{message}")
        super().__init__(message)


class UnsupportedChainException(ValueError):
    """
    Raised when an endpoint is called for a chain which is unsupported by that endpoint.
    For example, if an audit endpoint is called for a chain which does not have source code support.
    """

    def __init__(
        self,
        chain: str,
        message: str = "An exception occurred when an endpoint was called for an unsupported chain: {}.",
    ):
        logging.error(message.format(chain))
        super().__init__(message.format(chain))


class InvalidTokenAddressException(ValueError):
    """
    Raised when an endpoint is called for a token address which is invalid.
    For example, if an endpoint is called for a token address which does not have correct length.
    """

    def __init__(
        self,
        message: str = "An exception occurred while validating the provided token address.",
    ):
        logging.error(f"{message}")
        super().__init__(message)


class GoPlusDataException(Exception):
    """
    Raised when an API call to the GoPlus API fails.
    For example, if the endpoint has rate limited this application.
    """

    def __init__(
        self,
        chain,
        token_address,
        message="An exception occurred while fetching data from GoPlus for {} on chain {}.",
    ):
        logging.error(
            f"An exception occurred while fetching data from GoPlus for token {token_address} on chain {chain}."
        )
        super().__init__(message.format(token_address, chain))


class BlockExplorerDataException(Exception):
    """
    Raised when an API call to the block explorer API fails.
    For example, if the endpoint has rate limited this application.
    """

    def __init__(
        self,
        chain,
        token_address,
        message="An exception occurred while fetching data from the block explorer for {} on chain {}.",
    ):
        logging.error(
            f"An exception occurred while fetching data from the block explorer for token {token_address} on chain {chain}."
        )
        super().__init__(message.format(token_address, chain))


class DatabaseLoadFailureException(Exception):
    """
    Raised when a call to load data from DynamoDB fails.
    """

    def __init__(
        self,
        message="An exception occurred while attempting to fetch data from DynamoDB.",
    ):
        super().__init__(message)


class DatabaseInsertFailureException(Exception):
    """
    Raised when a call to insert data into DynamoDB fails.
    """

    def __init__(
        self,
        message="An exception occurred while attempting to insert data into DynamoDB.",
    ):
        super().__init__(message)


class OutputValidationError(Exception):
    """
    Raised when a call to format data into required output schemas fails due to ValidationErrors.
    For example, when a call to cast a response as a Pydantic object for pre-processing fails validation.
    """

    def __init__(
        self,
        message="An exception occured while attempting to create a Pydantic response.",
    ):
        logging.error(message)
        super().__init__(message)


class GoPlusAccessKeyLoadError(Exception):
    """
    Raised when an error occurs whilst loading the GoPlus access key.
    """

    def __init__(
        self,
        message="An exception occured whilst loading the GoPlus access key from the file.",
    ):
        logging.error(message)
        super().__init__(message)


class GoPlusAccessKeyRefreshError(Exception):
    """
    Raised when an error occurs whilst refreshing the GoPlus access key.
    """

    def __init__(
        self, message="An exception occured whilst refreshing the GoPlus access key."
    ):
        logging.error(message)
        super().__init__(message)


class SQSException(Exception):
    """
    Raised when an exception occurs whilst interacting with SQS.
    """

    def __init__(self, message="An exception occured whilst interacting with SQS."):
        logging.error(message)
        super().__init__(message)
