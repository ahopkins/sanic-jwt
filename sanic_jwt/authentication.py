import importlib
import jwt

from datetime import datetime
from datetime import timedelta
from sanic_jwt import exceptions


class BaseAuthentication(object):
    def __init__(self, app, authenticate):
        self.app = app
        self.authenticate = authenticate

    def store_refresh_token(self, *args, **kwargs):
        raise exceptions.RefreshTokenNotImplemented()

    def retrieve_refresh_token(self, *args, **kwargs):
        raise exceptions.RefreshTokenNotImplemented()


class SanicJWTAuthentication(BaseAuthentication):
    def _decode(self, token):
        secret = self._get_secret()
        algorithm = self._get_algorithm()
        return jwt.decode(token, secret, algorithms=[algorithm])

    def _get_algorithm(self):
        return self.app.config.SANIC_JWT_ALGORITHM

    def _get_payload(self, user):
        parts = self.app.config.SANIC_JWT_PAYLOAD_HANDLER.split('.')
        fn = parts.pop()
        module = importlib.import_module('.'.join(parts))
        method = getattr(module, fn)
        payload = method(self, user)

        delta = timedelta(seconds=self.app.config.SANIC_JWT_EXPIRATION_DELTA)
        exp = datetime.utcnow() + delta

        payload.update({
            'exp': exp
        })

        return payload

    def _get_secret(self):
        # TODO:
        # - Ability to have per user secrets
        return self.app.config.SANIC_JWT_SECRET

    def _get_token(self, request):
        if self.app.config.SANIC_JWT_COOKIE_SET:
            token = request.cookies.get(self.app.config.SANIC_JWT_COOKIE_TOKEN_NAME, None)
            if token is None:
                raise exceptions.MissingAuthorizationCookie()
            return token
        else:
            header = request.headers.get(self.app.config.SANIC_JWT_AUTHORIZATION_HEADER, None)
            if header:
                try:
                    prefix, token = header.split(' ')
                    if prefix != self.app.config.SANIC_JWT_AUTHORIZATION_HEADER_PREFIX:
                        raise Exception
                except Exception:
                    raise exceptions.InvalidAuthorizationHeader()

                return token

            raise exceptions.MissingAuthorizationHeader()

    def get_access_token(self, user):
        payload = self._get_payload(user)
        secret = self._get_secret()
        algorithm = self._get_algorithm()

        return jwt.encode(payload, secret, algorithm=algorithm)

    def get_refresh_token(self, user):
        refresh_token = '123456789'
        self.store_refresh_token(user=user, refresh_token=refresh_token)
        return refresh_token

    def is_authenticated(self, request, *args, **kwargs):
        try:
            is_valid, _, __ = self.verify(request, *args, **kwargs)
        except Exception:
            raise exceptions.Unauthorized()

        return is_valid

    def verify(self, request, return_payload=False, *args, **kwargs):
        token = self._get_token(request)
        is_valid = True
        reason = None

        try:
            payload = self._decode(token)
        except jwt.exceptions.ExpiredSignatureError:
            is_valid = False
            reason = 'Signature has expired'

        if return_payload:
            return payload

        status = 200 if is_valid else 400

        return is_valid, status, reason

    def extract_payload(self, request, *args, **kwargs):
        try:
            payload = self.verify(request, return_payload=True, *args, **kwargs)
        except Exception:
            raise exceptions.Unauthorized()

        return payload
