import logging
import inspect
from datetime import datetime, timedelta

import jwt

from . import exceptions, utils

logger = logging.getLogger(__name__)
claim_label = {"iss": "issuer", "iat": "iat", "nbf": "nbf", "aud": "audience"}


class BaseAuthentication:

    def __init__(self, app, config):
        self.app = app
        self.claims = ["exp"]
        self.config = config

    async def build_payload(self, user, *args, **kwargs):
        uid = self.config.user_id()
        if isinstance(user, dict):
            user_id = user.get(uid)
        elif hasattr(user, "to_dict"):
            _to_dict = await utils.call(user.to_dict)
            user_id = _to_dict.get(uid)
        else:
            raise exceptions.InvalidRetrieveUserObject()

        return {uid: user_id}

    async def add_claims(self, payload, *args, **kwargs):
        delta = timedelta(seconds=self.config.expiration_delta())
        exp = datetime.utcnow() + delta
        additional = {"exp": exp}

        for option in ["iss", "iat", "nbf", "aud"]:
            setting = "claim_{}".format(option.lower())
            if setting in self.config:
                attr = getattr(self.config, setting)()
                if attr:
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


class Authentication(BaseAuthentication):

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
                setting = "claim_{}".format(claim.upper())
                if setting in self.config:
                    value = getattr(self.config, setting)
                    kwargs.update({claim_label[claim]: value()})

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
            raise exceptions.MissingRegisteredClaim(missing=missing)

        return payload

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

    def _get_token(self, request, refresh_token=False):
        """
        Extract a token from a request object.
        """
        if self.config.cookie_set():
            cookie_token_name_key = "cookie_access_token_name" if refresh_token is False else "cookie_refresh_token_name"
            cookie_token_name = getattr(self.config, cookie_token_name_key)
            token = request.cookies.get(cookie_token_name(), None)
            if token is not None:
                return token

            else:
                if self.config.cookie_strict():
                    raise exceptions.MissingAuthorizationCookie()

        header = request.headers.get(self.config.authorization_header(), None)

        if header is not None:
            header_prefix_key = "authorization_header_prefix"
            header_prefix = getattr(self.config, header_prefix_key)
            try:
                prefix, token = header.split(" ")
                if prefix != header_prefix():
                    raise Exception

            except Exception:
                raise exceptions.InvalidAuthorizationHeader()

            if refresh_token:
                token = request.json.get(self.config.refresh_token_name())

            return token

        raise exceptions.MissingAuthorizationHeader()

    async def _get_refresh_token(self, request):
        """
        Extract a refresh token from a request object.
        """
        return self._get_token(request, refresh_token=True)

    async def _get_user_id(self, user):
        uid = self.config.user_id()
        if isinstance(user, dict):
            user_id = user.get(uid)
        elif hasattr(user, "to_dict"):
            _to_dict = await utils.call(user.to_dict)
            user_id = _to_dict.get(uid)
        else:
            raise exceptions.InvalidRetrieveUserObject()

        return user_id

    async def get_access_token(self, user):
        """
        Generate an access token for a given user.
        """
        payload = await self._get_payload(user)
        secret = self._get_secret(True)
        algorithm = self._get_algorithm()

        return jwt.encode(payload, secret, algorithm=algorithm).decode("utf-8")

    async def get_refresh_token(self, request, user):
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

    def is_authenticated(self, request, *args, **kwargs):
        try:
            is_valid, status, reasons = self.verify(request, *args, **kwargs)
        except Exception as e:
            if self.config.debug():
                raise Exception(e)

            else:
                raise exceptions.Unauthorized()

        return is_valid, status, reasons

    def verify(
        self, request, return_payload=False, verify=True, *args, **kwargs
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

    async def retrieve_refresh_token_from_request(self, request):
        return await self._get_refresh_token(request)

    def retrieve_scopes(self, request):
        """
        Extract scopes from a request object.
        """
        payload = self.extract_payload(request)
        scopes_attribute = self.config.scopes_name()
        return payload.get(scopes_attribute, None)

    def extract_payload(self, request, verify=True, *args, **kwargs):
        """
        Extract a payload from a request object.
        """
        payload = self.verify(
            request, return_payload=True, verify=verify, *args, **kwargs
        )
        return payload
