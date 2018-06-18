import inspect
import logging
from datetime import datetime, timedelta
import warnings
import jwt

from . import exceptions, utils

logger = logging.getLogger(__name__)
claim_label = {"iss": "issuer", "iat": "iat", "nbf": "nbf", "aud": "audience"}


class BaseAuthentication:

    def __init__(self, app, config):
        self.app = app
        self.claims = ["exp"]
        self.config = config

    async def _get_user_id(self, user, *, asdict=False):
        """
        Get a user_id from a user object. If `asdict` is True, will return
        it as a dict with `config.user_id` as key. The `asdict` keyword
        defaults to `False`.
        """
        uid = self.config.user_id()
        if isinstance(user, dict):
            user_id = user.get(uid)
        elif hasattr(user, "to_dict"):
            _to_dict = await utils.call(user.to_dict)
            user_id = _to_dict.get(uid)
        else:
            raise exceptions.InvalidRetrieveUserObject()

        if asdict:
            return {uid: user_id}

        return user_id

    async def build_payload(self, user, *args, **kwargs):
        return await self._get_user_id(user, asdict=True)

    async def add_claims(self, payload, *args, **kwargs):
        """
        Injects standard claims into the payload for: exp, iss, iat, nbf, aud.
        """
        delta = timedelta(seconds=self.config.expiration_delta())
        exp = datetime.utcnow() + delta
        additional = {"exp": exp}

        for option in ["iss", "iat", "nbf", "aud"]:
            setting = "claim_{}".format(option.lower())
            if setting in self.config:
                attr = self.config.get(setting)
                if attr:
                    self.claims.append(option)
                    method_name = "build_claim_{}".format(option)
                    method = getattr(utils, method_name)
                    additional.update({option: method(attr, self.config)})

        payload.update(additional)

        return payload

    async def extend_payload(self, payload, user=None, *args, **kwargs):
        return payload

    async def store_refresh_token(self, *args, **kwargs):
        raise exceptions.RefreshTokenNotImplemented()  # noqa

    async def retrieve_refresh_token(self, *args, **kwargs):
        raise exceptions.RefreshTokenNotImplemented()  # noqa

    async def authenticate(self, *args, **kwargs):
        raise exceptions.AuthenticateNotImplemented()  # noqa

    async def add_scopes_to_payload(self, *args, **kwargs):
        raise exceptions.ScopesNotImplemented()  # noqa

    def override_scope_validator(  # noqa
        self,
        is_valid,
        required,
        user_scopes,
        require_all_actions,
        *args,
        **kwargs
    ):
        return is_valid

    def destructure_scopes(self, scopes, *args, **kwargs):  # noqa
        return scopes

    async def retrieve_user(self, *args, **kwargs):
        raise exceptions.MeEndpointNotSetup()  # noqa


class Authentication(BaseAuthentication):

    def _check_authentication(self, request, request_args, request_kwargs):
        """
        Checks a request object to determine if that request contains a valid,
        and authenticated JWT.

        It returns a tuple:
        1. Boolean whether the request is authenticated with a valid JWT
        2. HTTP status code
        3. Reasons (if any) for a potential authentication failure
        """
        try:
            is_valid, status, reasons = self._verify(
                request,
                request_args=request_args,
                request_kwargs=request_kwargs,
            )
        except Exception as e:
            logger.debug(e.args)
            raise exceptions.Unauthorized()

        return is_valid, status, reasons

    def _decode(self, token, verify=True):
        """
        Take a JWT and return a decoded payload. Optionally, will verify
        the claims on the token.
        """
        secret = self._get_secret()
        algorithm = self._get_algorithm()
        kwargs = {}

        for claim in self.claims:
            if claim != "exp":
                setting = "claim_{}".format(claim.lower())
                if setting in self.config:
                    value = self.config.get(setting)
                    kwargs.update({claim_label[claim]: value})

        kwargs["leeway"] = int(self.config.leeway())
        if "claim_aud" in self.config:
            kwargs["audience"] = self.config.claim_aud()
        if "claim_iss" in self.config:
            kwargs["issuer"] = self.config.claim_iss()

        decoded = jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
            verify=verify,
            options={"verify_exp": self.config.verify_exp()},
            **kwargs
        )
        return decoded

    def _get_algorithm(self):
        return self.config.algorithm()

    async def _get_payload(self, user):
        """
        Given a user object, create a payload and extend it as configured.
        """
        payload = await utils.call(self.build_payload, user)

        if (
            not isinstance(payload, dict)
            or self.config.user_id() not in payload
        ):
            raise exceptions.InvalidPayload

        payload = await utils.call(self.add_claims, payload)

        extend_payload_args = inspect.getargspec(self.extend_payload)
        args = [payload]
        if "user" in extend_payload_args.args:
            args.append(user)
        payload = await utils.call(self.extend_payload, *args)

        if self.config.scopes_enabled():
            scopes = await utils.call(self.add_scopes_to_payload, user)
            if not isinstance(scopes, (tuple, list)):
                scopes = [scopes]
            payload[self.config.scopes_name()] = scopes

        missing = [x for x in self.claims if x not in payload]
        if missing:
            logger.debug("")
            raise exceptions.MissingRegisteredClaim(missing=missing)

        return payload

    async def _get_refresh_token(self, request):
        """
        Extract a refresh token from a request object.
        """
        return self._get_token(request, refresh_token=True)

    def _get_secret(self, encode=False):
        # TODO:
        # - Ability to have per user secrets
        if not hasattr(self, "_is_asymmetric"):
            self._is_asymmetric = utils.algorithm_is_asymmetric(
                self._get_algorithm()
            )
        if self._is_asymmetric and encode:
            return self.config.private_key()

        return self.config.secret()

    def _get_token_from_cookies(self, request, refresh_token):
        """
        Extract the token if present inside the request cookies.
        """
        if refresh_token:
            cookie_token_name_key = "cookie_refresh_token_name"
        else:
            cookie_token_name_key = "cookie_access_token_name"
        cookie_token_name = getattr(self.config, cookie_token_name_key)
        return request.cookies.get(cookie_token_name(), None)

    def _get_token_from_headers(self, request, refresh_token):
        """
        Extract the token if present inside the headers of a request.
        """
        header = request.headers.get(self.config.authorization_header(), None)

        if header is None:
            return None

        else:
            header_prefix_key = "authorization_header_prefix"
            header_prefix = getattr(self.config, header_prefix_key)
            if header_prefix():
                try:
                    prefix, token = header.split(" ")
                    if prefix != header_prefix():
                        raise Exception

                except Exception:
                    raise exceptions.InvalidAuthorizationHeader()

            else:
                token = header

            if refresh_token:
                token = request.json.get(self.config.refresh_token_name())

            return token

    def _get_token_from_query_string(self, request, refresh_token):
        """
        Extract the token if present from the request args.
        """
        if refresh_token:
            query_string_token_name_key = "query_string_refresh_token_name"
        else:
            query_string_token_name_key = "query_string_access_token_name"
        query_string_token_name = getattr(
            self.config, query_string_token_name_key
        )
        return request.raw_args.get(query_string_token_name(), None)

    def _get_token(self, request, refresh_token=False):
        """
        Extract a token from a request object.
        """
        if self.config.cookie_set():
            token = self._get_token_from_cookies(request, refresh_token)
            if token is not None:
                return token

            else:
                if self.config.cookie_strict():
                    raise exceptions.MissingAuthorizationCookie()

        if self.config.query_string_set():
            token = self._get_token_from_query_string(request, refresh_token)
            if token is not None:
                return token

            else:
                if self.config.query_string_strict():
                    raise exceptions.MissingAuthorizationQueryArg()

        token = self._get_token_from_headers(request, refresh_token)
        if token is not None:
            return token

        raise exceptions.MissingAuthorizationHeader()

    def _verify(
        self,
        request,
        return_payload=False,
        verify=True,
        request_args=None,
        request_kwargs=None,
        *args,
        **kwargs
    ):
        """
        Verify that a request object is authenticated.
        """
        token = self._get_token(request)
        is_valid = True
        reason = None

        try:
            payload = self._decode(token, verify=verify)
        except (
            jwt.exceptions.ExpiredSignatureError,
            jwt.exceptions.InvalidIssuerError,
            jwt.exceptions.ImmatureSignatureError,
            jwt.exceptions.InvalidIssuedAtError,
            jwt.exceptions.InvalidAudienceError,
        ) as e:
            is_valid = False
            reason = list(e.args)
            payload = None
            status = 403

        if return_payload:
            return payload

        status = 200 if is_valid else status

        return is_valid, status, reason

    def extract_payload(self, request, verify=True, *args, **kwargs):
        """
        Extract a payload from a request object.
        """
        payload = self._verify(
            request, return_payload=True, verify=verify, *args, **kwargs
        )
        return payload

    def extract_scopes(self, request):
        """
        Extract scopes from a request object.
        """
        payload = self.extract_payload(request)
        scopes_attribute = self.config.scopes_name()
        return payload.get(scopes_attribute, None)

    def extract_user_id(self, request):
        """
        Extract a user id from a request object.
        """
        payload = self.extract_payload(request)
        user_id_attribute = self.config.user_id()
        return payload.get(user_id_attribute, None)

    async def generate_access_token(self, user):
        """
        Generate an access token for a given user.
        """
        payload = await self._get_payload(user)
        secret = self._get_secret(True)
        algorithm = self._get_algorithm()

        return jwt.encode(payload, secret, algorithm=algorithm).decode("utf-8")

    async def generate_refresh_token(self, request, user):
        """
        Generate a refresh token for a given user.
        """
        refresh_token = await utils.call(self.config.generate_refresh_token())
        user_id = await self._get_user_id(user)
        await utils.call(
            self.store_refresh_token,
            user_id=user_id,
            refresh_token=refresh_token,
            request=request,
        )
        return refresh_token

    async def get_access_token(self, user):  # noqa
        warnings.warn(
            "Using sanic_jwt.Authentication.get_access_token(), "
            "which will be depracated in the future. Switch to "
            "sanic_jwt.Authentication.generate_access_token()."
        )
        return await self.generate_access_token(user)

    async def get_refresh_token(self, request, user):  # noqa
        warnings.warn(
            "Using sanic_jwt.Authentication.get_refresh_token(), "
            "which will be depracated in the future. Switch to "
            "sanic_jwt.Authentication.generate_refresh_token()."
        )
        return await self.generate_refresh_token(request, user)

    def is_authenticated(self, request):
        """
        Checks a request object to determine if that request contains a valid,
        and authenticated JWT.
        """
        try:
            is_valid, *_ = self._verify(request)
        except Exception as e:
            logger.debug(e.args)
            is_valid = False

        return is_valid

    async def retrieve_refresh_token_from_request(self, request):
        return await self._get_refresh_token(request)

    def retrieve_scopes(self, request):  # noqa
        warnings.warn(
            "Using sanic_jwt.Authentication.retrieve_scopes(), "
            "which will be depracated in the future. Switch to "
            "sanic_jwt.Authentication.extract_scopes()."
        )
        return self.extract_scopes(request)
