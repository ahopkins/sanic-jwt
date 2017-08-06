import importlib
import jwt

from sanic_jwt import exceptions


class BaseAuthentication(object):
    def __init__(self, app, authenticate):
        self.app = app
        self.authenticate = authenticate


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

        return payload

    def _get_secret(self):
        return self.app.config.SANIC_JWT_SECRET

    def _get_token(self, request):
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

    def is_authenticated(self, request, *args, **kwargs):
        try:
            is_valid, _, __ = self.verify(request, *args, **kwargs)
        except Exception:
            raise exceptions.Unauthorized()

        return is_valid

    def verify(self, request, *args, **kwargs):
        token = self._get_token(request)
        is_valid = True
        reason = None

        try:
            self._decode(token)
        except jwt.exceptions.ExpiredSignatureError:
            is_valid = False
            reason = 'Signature has expired'

        status = 200 if is_valid else 400

        return is_valid, status, reason
