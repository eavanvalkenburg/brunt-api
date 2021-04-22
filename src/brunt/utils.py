"""Util classes for Brunt."""
from enum import Enum


class RequestTypes(Enum):
    """Enum class for requests."""

    POST = "POST"
    GET = "GET"
    PUT = "PUT"
