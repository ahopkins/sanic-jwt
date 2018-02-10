import jwt

from datetime import datetime
from datetime import timedelta
from sanic_jwt import exceptions
from sanic_jwt import utils

claim_label = {
    'iss': 'issuer',
    'iat': 'iat',
    'nbf': 'nbf',
    'aud': 'audience',
}


class BaseAuthentication(object):
    add_scopes_to_payload = None

    def __init__(self, app):
        self.app = app
        # self.authenticate = authenticate
        self.claims = ['exp']

    async def build_payload(self, user, *args, **kwargs):
        if isinstance(user, dict):
            user_id = user.get(self.app.config.SANIC_JWT_USER_ID)
        elif hasattr(user, 'to_dict'):
            _to_dict = await utils.call(user.to_dict)
            user_id = _to_dict.get(self.app.config.SANIC_JWT_USER_ID)
        else:
            raise exceptions.InvalidRetrieveUserObject()

        return {
            'user_id': user_id,
        }

    async def extend_payload(self, payload, *args, **kwargs):
        delta = timedelta(seconds=self.app.config.SANIC_JWT_EXPIRATION_DELTA)
        exp = datetime.utcnow() + delta
        additional = {
            'exp': exp
        }

        for option in ['iss', 'iat', 'nbf', 'aud', ]:
            setting = 'SANIC_JWT_CLAIM_{}'.format(option.upper())
            attr = getattr(self.app.config, setting, False)
            if attr:
                method_name = 'build_claim_{}'.format(option)
                method = getattr(utils, method_name)
                additional.update({option: method(attr, self.app.SANIC_JWT_config)})

        payload.update(additional)

        return payload

    # async def store_refresh_token(self, *args, **kwargs):
    #     raise exceptions.RefreshTokenNotImplemented()  # noqa

    # async def retrieve_refresh_token(self, *args, **kwargs):
    #     raise exceptions.RefreshTokenNotImplemented()  # noqa

    # async def authenticate(self, *args, **kwargs):
    #     raise exceptions.AuthenticateNotImplemented()  # noqa


class Authentication(BaseAuthentication):
    def setup_claims(self, *args, **kwargs):

        optional = ['iss', 'iat', 'nbf', 'aud', ]

        # print('claims', self.claims)
        for option in optional:
            setting = 'claim_{}'.format(option.upper())
            # print(setting, getattr(self.app.config, SANIC_JWT_SETTING, False))
            if getattr(self.app.config, setting, False):
                self.claims.append(option)
        # print(self.claims)

    def _decode(self, token, verify=True):
        secret = self._get_secret()
        algorithm = self._get_algorithm()
        kwargs = {}

        for claim in self.claims:
            if claim != 'exp':
                setting = 'claim_{}'.format(claim.upper())
                value = getattr(self.app.config, setting, False)
                kwargs.update({claim_label[claim]: value})

        # TODO:
        # - Add leeway=self.app.config.SANIC_JWT_LEEWAY to jwt.decode
        # verify_exp
        return jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
            verify=verify,
            options={
                'verify_exp': self.app.config.SANIC_JWT_VERIFY_EXP
            },
            **kwargs
        )

    def _get_algorithm(self):
        return self.app.config.SANIC_JWT_ALGORITHM

    async def _get_payload(self, user):
        payload = await utils.call(
            self.build_payload, user)
        # TODO:
        # - Add verification check to make sure payload is a dict
        #   with a `user_id` key
        payload = await utils.call(
            self.extend_payload, payload)

        if self.add_scopes_to_payload is not None:
            scopes = await utils.call(
                self.add_scopes_to_payload, user)
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
        cookie_token_name_key = 'SANIC_JWT_COOKIE_ACCESS_TOKEN_NAME' \
            if refresh_token is False else \
            'SANIC_JWT_COOKIE_REFRESH_TOKEN_NAME'
        cookie_token_name = getattr(self.app.config, cookie_token_name_key)
        header_prefix_key = 'SANIC_JWT_AUTHORIZATION_HEADER_PREFIX'
        header_prefix = getattr(self.app.config, header_prefix_key)

        if self.app.config.SANIC_JWT_COOKIE_SET:
            token = request.cookies.get(cookie_token_name, None)
            if token:
                return token
            else:
                if self.app.config.SANIC_JWT_COOKIE_STRICT:
                    raise exceptions.MissingAuthorizationCookie()

        header = request.headers.get(
            self.app.config.SANIC_JWT_AUTHORIZATION_HEADER, None)
        if header:
            try:
                prefix, token = header.split(' ')
                if prefix != header_prefix:
                    raise Exception
            except Exception:
                raise exceptions.InvalidAuthorizationHeader()

            if refresh_token:
                token = request.json.get(
                    self.app.config.SANIC_JWT_REFRESH_TOKEN_NAME)

            return token

        raise exceptions.MissingAuthorizationHeader()

    async def _get_refresh_token(self, request):
        return self._get_token(request, refresh_token=True)

    async def _get_user_id(self, user):
        if isinstance(user, dict):
            user_id = user.get(self.app.config.SANIC_JWT_USER_ID)
        elif hasattr(user, 'to_dict'):
            _to_dict = await utils.call(user.to_dict)
            user_id = _to_dict.get(self.app.config.SANIC_JWT_USER_ID)
        else:
            raise exceptions.InvalidRetrieveUserObject()
        return user_id

    async def get_access_token(self, user):
        payload = await self._get_payload(user)
        secret = self._get_secret()
        algorithm = self._get_algorithm()

        return jwt.encode(payload, secret, algorithm=algorithm)

    async def get_refresh_token(self, request, user):
        refresh_token = utils.generate_token()
        user_id = await self._get_user_id(user)
        await utils.call(
            self.store_refresh_token,
            user_id=user_id,
            refresh_token=refresh_token,
            request=request)
        return refresh_token

    def is_authenticated(self, request, *args, **kwargs):
        try:
            is_valid, _, __ = self.verify(request, *args, **kwargs)
        except Exception as e:
            if self.app.config.SANIC_JWT_DEBUG:
                raise Exception(e)
            else:
                raise exceptions.Unauthorized()

        return is_valid

    def verify(self, request, return_payload=False, verify=True, *args,
               **kwargs):
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

        return is_valid, status, reason

    async def retrieve_refresh_token_from_request(self, request):
        return await self._get_refresh_token(request)

    def retrieve_scopes(self, request):
        payload = self.extract_payload(request)
        scopes_attribute = request.app.config.SANIC_JWT_SCOPES_NAME
        return payload.get(scopes_attribute, None)

    def extract_payload(self, request, verify=True, *args, **kwargs):
        try:
            payload = self.verify(request, return_payload=True, verify=verify,
                                  *args, **kwargs)
        except Exception as e:
            raise e
            # raise exceptions.Unauthorized()

        return payload
