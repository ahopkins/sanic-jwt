from sanic.exceptions import SanicException
from sanic.exceptions import Unauthorized as SanicUnauthorized
from sanic.exceptions import add_status_code


class SanicJWTException(SanicException):
    pass


@add_status_code(401)
class AuthenticationFailed(SanicJWTException):

    def __init__(self, message='Authentication failed.', **kwargs):
        super().__init__(message, **kwargs)


@add_status_code(400)
class MissingAuthorizationHeader(SanicJWTException):

    def __init__(self, message='Authorization header not present.', **kwargs):
        super().__init__(message, **kwargs)


@add_status_code(400)
class MissingAuthorizationCookie(SanicJWTException):

    def __init__(self, message='Authorization cookie not present.', **kwargs):
        super().__init__(message, **kwargs)


@add_status_code(400)
class InvalidAuthorizationHeader(SanicJWTException):

    def __init__(self, message='Authorization header is invalid.', **kwargs):
        super().__init__(message, **kwargs)


@add_status_code(500)
class AuthenticateNotImplemented(SanicJWTException):

    def __init__(
        self,
        message='Sanic JWT initialized without providing an authenticate '
        'method.',
            **kwargs):
        super().__init__(message, **kwargs)


@add_status_code(500)
class RefreshTokenNotImplemented(SanicJWTException):

    def __init__(self, message="Refresh tokens have not been enabled.", **kwargs):
        super().__init__(message, **kwargs)


@add_status_code(500)
class ScopesNotImplemented(SanicJWTException):

    def __init__(
        self,
        message='Scopes have not been enabled. Initialize with '
        'add_scopes_to_payload to provide scoping.',
            **kwargs):
        super().__init__(message, **kwargs)


@add_status_code(500)
class MissingRegisteredClaim(SanicJWTException):

    def __init__(
            self,
            message='One or more claims have been registered, but your '
                    'SANIC_JWT_HANDLER_PAYLOAD_EXTEND does not supply them. ',
            missing=None,
            **kwargs):
        if missing:
            message += str(missing)
        super().__init__(message, **kwargs)


@add_status_code(500)
class MeEndpointNotSetup(SanicJWTException):

    def __init__(
        self,
        message='/me endpoint has not been setup. Pass retrieve_user if '
        'you with to proceeed.',
            **kwargs):
        super().__init__(message, **kwargs)


@add_status_code(500)
class InvalidRetrieveUserObject(SanicJWTException):

    def __init__(
        self,
        message='The retrieve_user method should return either a dict or '
        'an object with a to_dict method.',
            **kwargs):
        super().__init__(message, **kwargs)


@add_status_code(500)
class InitializationFailure(SanicJWTException):

    def __init__(
        self,
        message='Sanic JWT was not initialized properly. It must be '
        'instantiated on a sanic.Sanic or sanic.Blueprint '
        'instance.',
            **kwargs):
        super().__init__(message, **kwargs)


class Unauthorized(SanicJWTException, SanicUnauthorized):

    def __init__(self, message="Auth required.", **kwargs):
        super().__init__(message, scheme="Bearer", **kwargs)


class InvalidClassViewsFormat(SanicJWTException):

    def __init__(
        self,
        message='class_views should follow this format (\'<SOME ROUTE>\', '
        'ClassInheritedFromHTTPMethodView)',
            **kwargs):
        super().__init__(message, **kwargs)


class InvalidConfiguration(SanicJWTException):

    def __init__(self, message="", **kwargs):
        message = 'An invalid setting was , **kwargspassed to the Sanic JWT ' \
                  'configuration: ' + str(message)
        super().__init__(message)


class InvalidPayload(SanicJWTException):

    def __init__(self, message="", **kwargs):
        message = 'Payload must be a dicti, **kwargsonary with a key mapped to ' \
                  'SANIC_JWT_USER_ID'
        super().__init__(message)


class RequiredKeysNotFound(SanicJWTException):

    def __init__(
        self,
        message='You must provide both (valid) SANIC_JWT_PUBLIC_KEY and '
        'SANIC_JWT_PRIVATE_KEY when using asymmetric '
        'cryptographic algorithms like RS*, EC* or PS*',
            **kwargs):
        super().__init__(message, **kwargs)


class ProvidedPathNotFound(SanicJWTException):

    def __init__(self,
                 message='The Path object given is not a valid file',
                 **kwargs):
        super().__init__(message, **kwargs)
