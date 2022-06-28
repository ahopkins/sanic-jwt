__version__ = "1.8.0"
__author__ = "Adam Hopkins"
__credits__ = "Richard Kuesters"

import logging

from .authentication import Authentication
from .claim import Claim
from .configuration import Configuration
from .decorators import inject_user, protected, scoped
from .endpoints import BaseEndpoint
from .initialization import Initialize, initialize
from .responses import Responses

logging.getLogger(__name__).addHandler(logging.NullHandler())


__all__ = [
    "Authentication",
    "BaseEndpoint",
    "Claim",
    "Configuration",
    "initialize",
    "Initialize",
    "inject_user",
    "protected",
    "Responses",
    "scoped",
]
