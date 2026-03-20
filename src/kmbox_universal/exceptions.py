"""Exceptions raised by kmbox-universal."""


class KMBoxError(Exception):
    """Base KMBox exception."""


class KMBoxTimeoutError(KMBoxError):
    """Raised when the device does not reply before timeout."""


class KMBoxProtocolError(KMBoxError):
    """Raised when a response does not match the expected command/index."""
