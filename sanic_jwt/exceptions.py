from sanic.exceptions import SanicException
from sanic.exceptions import Unauthorized as SanicUnauthorized
from sanic.exceptions import add_status_code


@add_status_code(401)
class AuthenticationFailed(SanicException):
    def __init__(self, message="Authentication failed."):
        super().__init__(message)


@add_status_code(400)
class MissingAuthorizationHeader(SanicException):
    def __init__(self, message="Authorization header not present."):
        super().__init__(message)


@add_status_code(400)
class MissingAuthorizationCookie(SanicException):
    def __init__(self, message="Authorization cookie not present."):
        super().__init__(message)


@add_status_code(400)
class InvalidAuthorizationHeader(SanicException):
    def __init__(self, message="Authorization header is invalid."):
        super().__init__(message)


@add_status_code(500)
class RefreshTokenNotImplemented(SanicException):
    def __init__(self, message="Refresh tokens have not been enabled."):
        super().__init__(message)


@add_status_code(500)
class MissingRegisteredClaim(SanicException):
    def __init__(self, message="One or more claims have been registered, but your SANIC_JWT_HANDLER_PAYLOAD_EXTEND does not supply them. ", missing=None):
        if missing:
            message += str(missing)
        super().__init__(message)


@add_status_code(500)
class MeEndpointNotSetup(SanicException):
    def __init__(self, message="/me endpoint has not been setup. Pass retrieve_user if you with to proceeed."):
        super().__init__(message)


class Unauthorized(SanicUnauthorized):
    def __init__(self):
        super().__init__("Auth required.", "Bearer")
