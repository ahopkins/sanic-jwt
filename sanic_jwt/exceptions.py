from sanic.exceptions import SanicException
from sanic.exceptions import Unauthorized as SanicUnauthorized
from sanic.exceptions import add_status_code


class SanicJWTException(SanicException):
    pass


@add_status_code(401)
class AuthenticationFailed(SanicJWTException):
    def __init__(self, message="Authentication failed."):
        super().__init__(message)


@add_status_code(400)
class MissingAuthorizationHeader(SanicJWTException):
    def __init__(self, message="Authorization header not present."):
        super().__init__(message)


@add_status_code(400)
class MissingAuthorizationCookie(SanicJWTException):
    def __init__(self, message="Authorization cookie not present."):
        super().__init__(message)


@add_status_code(400)
class InvalidAuthorizationHeader(SanicJWTException):
    def __init__(self, message="Authorization header is invalid."):
        super().__init__(message)


@add_status_code(500)
class AuthenticateNotImplemented(SanicJWTException):
    def __init__(self, message="Sanic JWT initialized without providing an authenticate method."):
        super().__init__(message)


@add_status_code(500)
class RefreshTokenNotImplemented(SanicJWTException):
    def __init__(self, message="Refresh tokens have not been enabled."):
        super().__init__(message)


@add_status_code(500)
class MissingRegisteredClaim(SanicJWTException):
    def __init__(
        self,
        message="One or more claims have been registered, but your SANIC_JWT_HANDLER_PAYLOAD_EXTEND does not supply them. ",
        missing=None
    ):
        if missing:
            message += str(missing)
        super().__init__(message)


@add_status_code(500)
class MeEndpointNotSetup(SanicJWTException):
    def __init__(
        self,
        message="/me endpoint has not been setup. Pass retrieve_user if you with to proceeed."
    ):
        super().__init__(message)


@add_status_code(500)
class InvalidRetrieveUserObject(SanicJWTException):

    def __init__(
        self,
        message="The retrieve_user method should return either a dict or an object with a to_dict method."
    ):
        super().__init__(message)


@add_status_code(500)
class InitializationFailure(SanicJWTException):
    def __init__(self, message="Sanic JWT was not initialized properly. It must be instantiated on a sanic.Sanic or sanic.Blueprint instance."):
        super().__init__(message)


class Unauthorized(SanicJWTException, SanicUnauthorized):
    def __init__(self):
        super().__init__("Auth required.", scheme="Bearer")


class InvalidClassViewsFormat(SanicJWTException):
    def __init__(
        self,
        message="class_views should follow this format ('<SOME ROUTE>', ClassInheritedFromHTTPMethodView)"
    ):
        super().__init__(message)


class InvalidConfiguration(SanicJWTException):
    def __init__(self, message=""):
        message = "An invalid setting was passed to the Sanic JWT configuration: " + str(message)
        super().__init__(message)
