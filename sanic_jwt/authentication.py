import jwt

from sanic_jwt import exceptions, utils


claim_label = {
    'iss': 'issuer',
    'iat': 'iat',
    'nbf': 'nbf',
    'aud': 'audience',
}


class BaseAuthentication(object):
    def __init__(self, app, config):
        self.app = app
        self.config = config
        # self.authenticate = authenticate
        self.claims = ['exp']

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
            # print(setting, getattr(self.app.config, setting, False))
            if getattr(self.config, setting, False):
                self.claims.append(option)
        # print(self.claims)

    def _decode(self, token, verify=True):
        secret = self._get_secret()
        algorithm = self._get_algorithm()
        kwargs = {}

        for claim in self.claims:
            if claim != 'exp':
                setting = 'claim_{}'.format(claim.upper())
                value = getattr(self.config, setting, False)
                kwargs.update({claim_label[claim]: value})

        # TODO:
        # - Add leeway=self.config.leeway to jwt.decode
        # verify_exp
        return jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
            verify=verify,
            options={
                'verify_exp': self.config.verify_exp
            },
            **kwargs
        )

    def _get_algorithm(self):
        return self.config.algorithm

    async def _get_payload(self, user):
        payload = await utils.execute_handler(
            self.config.handler_payload, self, user)
        # TODO:
        # - Add verification check to make sure payload is a dict
        #   with a `user_id` key
        payload = await utils.execute_handler(
            self.config.handler_payload_extend, self, payload)

        if self.config.handler_payload_scopes is not None:
            scopes = await utils.execute_handler(
                self.config.handler_payload_scopes, user)
            if not isinstance(scopes, (tuple, list)):
                scopes = [scopes]
            payload[self.config.scopes_name] = scopes

        missing = [x for x in self.claims if x not in payload]
        if missing:
            raise exceptions.MissingRegisteredClaim(missing=missing)

        return payload

    def _get_secret(self):
        # TODO:
        # - Ability to have per user secrets
        return self.config.secret

    def _get_token(self, request, refresh_token=False):
        cookie_token_name_key = 'cookie_access_token_name' \
            if refresh_token is False else \
            'cookie_refresh_token_name'
        cookie_token_name = getattr(self.config, cookie_token_name_key)
        header_prefix_key = 'authorization_header_prefix'
        header_prefix = getattr(self.config, header_prefix_key)

        if self.config.cookie_set:
            token = request.cookies.get(cookie_token_name, None)
            if token:
                return token
            else:
                if self.config.cookie_strict:
                    raise exceptions.MissingAuthorizationCookie()

        header = request.headers.get(
            self.config.authorization_header, None)
        if header:
            try:
                prefix, token = header.split(' ')
                if prefix != header_prefix:
                    raise Exception
            except Exception:
                raise exceptions.InvalidAuthorizationHeader()

            if refresh_token:
                token = request.json.get(
                    self.config.refresh_token_name)

            return token

        raise exceptions.MissingAuthorizationHeader()

    async def _get_refresh_token(self, request):
        return self._get_token(request, refresh_token=True)

    def _get_user_id(self, user):
        if isinstance(user, dict):
            user_id = user.get(self.config.user_id)
        else:
            user_id = getattr(user, self.config.user_id)
        return user_id

    async def get_access_token(self, user):
        payload = await self._get_payload(user)
        secret = self._get_secret()
        algorithm = self._get_algorithm()

        return jwt.encode(payload, secret, algorithm=algorithm)

    async def get_refresh_token(self, request, user):
        refresh_token = utils.generate_token()
        user_id = self._get_user_id(user)
        await self.store_refresh_token(user_id=user_id,
                                       refresh_token=refresh_token,
                                       request=request)
        return refresh_token

    def is_authenticated(self, request, *args, **kwargs):
        try:
            is_valid, _, __ = self.verify(request, *args, **kwargs)
        except Exception:
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

        # print(is_valid, status, reason)

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
