import inspect
import logging
import warnings
from datetime import datetime, timedelta

import jwt

from . import exceptions, utils
from .exceptions import (
    InvalidCustomClaimError,
    InvalidVerification,
    InvalidVerificationError,
    SanicJWTException
)

logger = logging.getLogger(__name__)
claim_label = {"iss": "issuer", "iat": "iat", "nbf": "nbf", "aud": "audience"}


class BaseAuthentication:
    def __init__(self, app, config):
        self.app = app
        self.claims = ["exp"]
        self._extra_verifications = None
        self.config = config
        self._reasons = []
        self._custom_claims = set()

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

    async def add_claims(self, payload, user, *args, **kwargs):
        """
        Injects standard claims into the payload for: exp, iss, iat, nbf, aud.
        And, custom claims, if they exist
        """
        delta = timedelta(seconds=self.config.expiration_delta())
        exp = datetime.utcnow() + delta
        additional = {"exp": exp}

        for option in ["iss", "iat", "nbf", "aud"]:
            setting = "claim_{}".format(option.lower())
            if setting in self.config:  # noqa
                attr = self.config.get(setting)
                if attr:
                    self.claims.append(option)
                    method_name = "build_claim_{}".format(option)
                    method = getattr(utils, method_name)
                    additional.update({option: method(attr, self.config)})

        payload.update(additional)

        if self._custom_claims:
            custom_claims = {}
            for claim in self._custom_claims:
                custom_claims[claim.get_key()] = await utils.call(
                    claim.setup, payload, user
                )
            payload.update(custom_claims)

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
        raise exceptions.MeEndpointNotSetup  # noqa


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
            if self.config.debug():
                raise e

            args = e.args if isinstance(e, SanicJWTException) else []

            raise exceptions.Unauthorized(*args)

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
                if setting in self.config:  # noqa
                    value = self.config.get(setting)
                    kwargs.update({claim_label[claim]: value})

        kwargs["leeway"] = int(self.config.leeway())
        if "claim_aud" in self.config:  # noqa
            kwargs["audience"] = self.config.claim_aud()
        if "claim_iss" in self.config:  # noqa
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

        payload = await utils.call(self.add_claims, payload, user)

        extend_payload_args = inspect.getfullargspec(self.extend_payload)
        args = [payload]
        if "user" in extend_payload_args.args:
            args.append(user)
        payload = await utils.call(self.extend_payload, *args)

        if self.config.scopes_enabled():
            scopes = await utils.call(self.add_scopes_to_payload, user)
            if not isinstance(scopes, (tuple, list)):
                scopes = [scopes]
            payload[self.config.scopes_name()] = scopes

        claims = self.claims + [x.get_key() for x in self._custom_claims]
        missing = [x for x in claims if x not in payload]
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
        return request.args.get(query_string_token_name(), None)

    def _get_token(self, request, refresh_token=False):
        """
        Extract a token from a request object.
        """
        if self.config.cookie_set():
            token = self._get_token_from_cookies(request, refresh_token)
            if token:
                return token

            else:
                if self.config.cookie_strict():
                    raise exceptions.MissingAuthorizationCookie()

        if self.config.query_string_set():
            token = self._get_token_from_query_string(request, refresh_token)
            if token:
                return token

            else:
                if self.config.query_string_strict():
                    raise exceptions.MissingAuthorizationQueryArg()

        token = self._get_token_from_headers(request, refresh_token)

        if token:
            return token

        raise exceptions.MissingAuthorizationHeader()

    def _verify(
        self,
        request,
        return_payload=False,
        verify=True,
        raise_missing=False,
        request_args=None,
        request_kwargs=None,
        *args,
        **kwargs
    ):
        """
        Verify that a request object is authenticated.
        """
        try:
            token = self._get_token(request)
            is_valid = True
            reason = None
        except (
            exceptions.MissingAuthorizationCookie,
            exceptions.MissingAuthorizationQueryArg,
            exceptions.MissingAuthorizationHeader,
        ) as e:
            token = None
            is_valid = False
            reason = list(e.args)
            status = e.status_code if self.config.debug() else 401

            if raise_missing:
                if not self.config.debug():
                    e.status_code = 401
                raise e

        if token:
            try:
                payload = self._decode(token, verify=verify)

                if verify:
                    if self._extra_verifications:
                        self._verify_extras(payload)
                    if self._custom_claims:
                        self._verify_custom_claims(payload)
            except (
                jwt.exceptions.ExpiredSignatureError,
                jwt.exceptions.InvalidIssuerError,
                jwt.exceptions.ImmatureSignatureError,
                jwt.exceptions.InvalidIssuedAtError,
                jwt.exceptions.InvalidAudienceError,
                InvalidVerificationError,
                InvalidCustomClaimError,
            ) as e:
                # Make sure that the reasons all end with '.' for consistency
                reason = [
                    x if x.endswith(".") else "{}.".format(x)
                    for x in list(e.args)
                ]
                payload = None
                status = 401
                is_valid = False
            except jwt.exceptions.DecodeError as e:
                self._reasons = e.args
                # Make sure that the reasons all end with '.' for consistency
                reason = (
                    [
                        x if x.endswith(".") else "{}.".format(x)
                        for x in list(e.args)
                    ]
                    if self.config.debug()
                    else "Auth required."
                )
                logger.debug(e.args)
                is_valid = False
                payload = None
                status = 400 if self.config.debug() else 401
        else:
            payload = None

        if return_payload:
            return payload

        status = 200 if is_valid else status

        return is_valid, status, reason

    def _verify_extras(self, payload):
        for verification in self._extra_verifications:
            if not callable(verification):
                raise InvalidVerification()

            verified = verification(payload)
            if not isinstance(verified, bool):
                raise InvalidVerification()

            if verified is False:
                raise InvalidVerificationError()

    def _verify_custom_claims(self, payload):
        for claim in self._custom_claims:
            claim._verify(payload)

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
        if not payload:
            return None

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
        is_valid, *_ = self._verify(request)

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
