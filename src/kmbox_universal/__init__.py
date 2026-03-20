"""kmbox-universal public API."""

from .client import AbsoluteMouseConfig, KMBoxClient
from .exceptions import KMBoxError, KMBoxProtocolError, KMBoxTimeoutError
from .types import HidKey, KeyboardModifier, MouseButton

__all__ = [
    "AbsoluteMouseConfig",
    "HidKey",
    "KeyboardModifier",
    "KMBoxClient",
    "KMBoxError",
    "KMBoxProtocolError",
    "KMBoxTimeoutError",
    "MouseButton",
]
