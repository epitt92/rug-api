import logging


class CoinGeckoChartException(Exception):
    """
    Raised when an API call to the CoinGecko chart API fails.
    For example, if the endpoint has rate limited this application.
    """

    def __init__(
        self,
        chain,
        token_address,
        frequency,
        message="An exception occurred while fetching chart data from CoinGecko for {} on chain {} with frequency {}.",
    ):
        logging.error(message.format(token_address, chain, frequency))
        super().__init__(message.format(token_address, chain, frequency))
