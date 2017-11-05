import jwt

from sanic_jwt import exceptions, utils


claim_label = {
    'iss': 'issuer',
    'iat': 'iat',
    'nbf': 'nbf',
    'aud': 'audience',
}


class BaseAuthentication(object):
    def __init__(self, app, authenticate):
        self.app = app
        self.authenticate = authenticate
        self.claims = ['exp']

    def store_refresh_token(self, *args, **kwargs):
        raise exceptions.RefreshTokenNotImplemented()

    def retrieve_refresh_token(self, *args, **kwargs):
        raise exceptions.RefreshTokenNotImplemented()


class SanicJWTAuthentication(BaseAuthentication):
    def setup_claims(self, *args, **kwargs):

        optional = ['iss', 'iat', 'nbf', 'aud', ]

        # print('claims', self.claims)
        for option in optional:
            setting = 'SANIC_JWT_CLAIM_{}'.format(option.upper())
            # print(setting, getattr(self.app.config, setting, False))
            if getattr(self.app.config, setting, False):
                self.claims.append(option)
        # print(self.claims)

    def _decode(self, token, verify=True):
        secret = self._get_secret()
        algorithm = self._get_algorithm()
        kwargs = {}

        for claim in self.claims:
            if claim != 'exp':
                setting = 'SANIC_JWT_CLAIM_{}'.format(claim.upper())
                value = getattr(self.app.config, setting, False)
                kwargs.update({claim_label[claim]: value})

        return jwt.decode(token, secret, algorithms=[algorithm], verify=verify, **kwargs)

    def _get_algorithm(self):
        return self.app.config.SANIC_JWT_ALGORITHM

    async def _get_payload(self, user):
        payload = await utils.execute_handler(self.app.config.SANIC_JWT_HANDLER_PAYLOAD, self, user)
        # TODO:
        # - Add verification check to make sure payload is a dict with a `user_id` key
        payload = await utils.execute_handler(self.app.config.SANIC_JWT_HANDLER_PAYLOAD_EXTEND, self, payload)

        if self.app.config.SANIC_JWT_HANDLER_PAYLOAD_SCOPES is not None:
            scopes = await utils.execute_handler(self.app.config.SANIC_JWT_HANDLER_PAYLOAD_SCOPES, user)
            if not isinstance(scopes, (tuple, list)):
                scopes = [scopes]
            payload[self.app.config.SANIC_JWT_SCOPES_NAME] = scopes

        missing = [x for x in self.claims if x not in payload]
        if missing:
            raise exceptions.MissingRegisteredClaim(missing=missing)

        return payload

    def _get_secret(self):
        # TODO:
        # - Ability to have per user secrets
        return self.app.config.SANIC_JWT_SECRET

    def _get_token(self, request, refresh_token=False):
        cookie_token_name_key = 'SANIC_JWT_COOKIE_TOKEN_NAME' if refresh_token is False else 'SANIC_JWT_COOKIE_REFRESH_TOKEN_NAME'
        cookie_token_name = getattr(self.app.config, cookie_token_name_key)
        # header_prefix_key = 'SANIC_JWT_AUTHORIZATION_HEADER_PREFIX' if refresh_token is False else 'SANIC_JWT_AUTHORIZATION_HEADER_REFRESH_PREFIX'
        header_prefix_key = 'SANIC_JWT_AUTHORIZATION_HEADER_PREFIX'
        header_prefix = getattr(self.app.config, header_prefix_key)

        if self.app.config.SANIC_JWT_COOKIE_SET:
            token = request.cookies.get(cookie_token_name, None)
            if token is None:
                raise exceptions.MissingAuthorizationCookie()
            return token
        else:
            header = request.headers.get(self.app.config.SANIC_JWT_AUTHORIZATION_HEADER, None)
            if header:
                try:
                    prefix, token = header.split(' ')
                    # if prefix != self.app.config.SANIC_JWT_AUTHORIZATION_HEADER_PREFIX:
                    if prefix != header_prefix:
                        raise Exception
                except Exception:
                    raise exceptions.InvalidAuthorizationHeader()

                if refresh_token:
                    token = request.json.get(self.app.config.SANIC_JWT_REFRESH_TOKEN_NAME)

                return token

            raise exceptions.MissingAuthorizationHeader()

    def _get_refresh_token(self, request):
        return self._get_token(request, refresh_token=True)

    def _get_user_id(self, user):
        if isinstance(user, dict):
            user_id = user.get(self.app.config.SANIC_JWT_USER_ID)
        else:
            user_id = getattr(user, self.app.config.SANIC_JWT_USER_ID)
        return user_id

    async def get_access_token(self, user):
        payload = await self._get_payload(user)
        secret = self._get_secret()
        algorithm = self._get_algorithm()

        return jwt.encode(payload, secret, algorithm=algorithm)

    async def get_refresh_token(self, user):
        refresh_token = utils.generate_token()
        user_id = self._get_user_id(user)
        self.store_refresh_token(user_id=user_id, refresh_token=refresh_token)
        return refresh_token

    def is_authenticated(self, request, *args, **kwargs):
        try:
            is_valid, _, __ = self.verify(request, *args, **kwargs)
        except Exception:
            raise exceptions.Unauthorized()

        return is_valid

    def verify(self, request, return_payload=False, verify=True, *args, **kwargs):
        token = self._get_token(request)
        is_valid = True
        reason = None

        try:
            payload = self._decode(token, verify=verify)
        except jwt.exceptions.ExpiredSignatureError:
            is_valid = False
            reason = 'Signature has expired'
            payload = None
        except (
            jwt.exceptions.InvalidIssuerError,
            jwt.exceptions.ImmatureSignatureError,
            jwt.exceptions.InvalidIssuedAtError,
            jwt.exceptions.InvalidAudienceError,
        ) as e:
            is_valid = False
            reason = e.args
            payload = None

        if return_payload:
            return payload

        status = 200 if is_valid else 400

        # print(is_valid, status, reason)

        return is_valid, status, reason

    def retrieve_refresh_token_from_request(self, request):
        return self._get_refresh_token(request)

    def retrieve_scopes(self, request):
        payload = self.extract_payload(request)
        scopes_attribute = request.app.config.SANIC_JWT_SCOPES_NAME
        return payload.get(scopes_attribute, None)

    def extract_payload(self, request, verify=True, *args, **kwargs):
        try:
            payload = self.verify(request, return_payload=True, verify=verify, *args, **kwargs)
        except Exception as e:
            raise e
            # raise exceptions.Unauthorized()

        return payload
