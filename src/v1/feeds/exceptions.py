import logging

class TimestreamWriteException(Exception):
    """
    Raised when an exception occurs when attempting to write to Timestream.
    """
    def __init__(self, message: str):
        logging.error(f'{message}')
        super().__init__(message)


class TimestreamReadException(Exception):
    """
    Raised when an exception occurs when attempting to read to Timestream.
    """
    def __init__(self, message: str):
        logging.error(f'{message}')
        super().__init__(message)


class InvalidEventHash(ValueError):
    """
    Raised when the event hash input is invalid.
    """
    def __init__(self, event_hash: str, message: str):
        logging.error(f'Invalid Event Hash: {event_hash} input.')
        super().__init__(message)
