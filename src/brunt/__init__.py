"""Init for Brunt."""
import sys
from importlib.metadata import PackageNotFoundError, version  # pragma: no cover

try:
    __version__ = version(__name__)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

from .client import (  # pylint: disable=wrong-import-position
    BruntClient,
    BruntClientAsync,
)
from .thing import Thing  # pylint: disable=wrong-import-position
