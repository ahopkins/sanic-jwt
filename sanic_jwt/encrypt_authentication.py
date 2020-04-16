"""
This file has a JWT Implementation with encryption of Payload.

Usage is so easy. You must provide ENCRYPT_PASSWORD and (optionally
ENCRYPT_SALT) into the Sanic app config.

>>> from sanic import Sanic
>>> app = Sanic()
>>> app.config.ENCRYPT_PASSWORD = "ASDFAsdfkjalsdfjlkasdfjlkasdjflksa"
>>> import sanic_jwt import AuthenticationEncrypted, Initialize
>>> Initialize(app, authentication_class=AuthenticationEncrypted)

"""
import jwt
import json
import base64
import warnings

from functools import lru_cache

from jwt.utils import merge_dict
from jwt import PyJWT, DecodeError

from calendar import timegm
from datetime import datetime
from typing import Union, Mapping, Dict, Optional, List

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .authentication import Authentication, utils, claim_label


def _get_kdf(salt: str):

    @lru_cache()
    def _get_salt(_salt) -> bytes:
        if _salt:
            return _salt.encode("UTF.8")
        else:
            return b''

    return PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_get_salt(salt),
        iterations=100000,
        backend=default_backend())


@lru_cache(100)
def fernet_crypt(text: str or bytes, password: str, salt: str) -> bytes:
    kdf = _get_kdf(salt)

    f = Fernet(base64.urlsafe_b64encode(kdf.derive(bytes(password, "utf-8"))))

    return f.encrypt(bytes(text, "utf-8"))


@lru_cache(100)
def fernet_decrypt(text: bytes, password: str, salt: str) -> bytes:
    kdf = _get_kdf(salt)

    f = Fernet(
        base64.urlsafe_b64encode(kdf.derive(bytes(password, "utf-8"))))

    return f.decrypt(text)


class PyJWTPayloadEncrypt(PyJWT):
    header_type = 'JWT'

    def encode(self,
               payload: Union[Dict, bytes],
               key: str,
               algorithm: str = 'HS256',
               headers: Optional[Dict] = None,
               **kwargs):
        """

        :type json_encoder: object
        :type encrypt_password: str
        :type encrypt_salt: str
        """

        # Check that we get a mapping
        if not isinstance(payload, Mapping):
            raise TypeError('Expecting a mapping object, as JWT only supports '
                            'JSON objects as payloads.')

        json_encoder = kwargs.get("json_encoder", None)
        password = kwargs.get("encrypt_password", None)
        if not password:
            raise ValueError("Invalid encrypt password!")
        salt = kwargs.get("encrypt_salt", None)

        # Payload
        for time_claim in ['exp', 'iat', 'nbf']:
            # Convert datetime to a intDate value in known time-format claims
            if isinstance(payload.get(time_claim), datetime):
                payload[time_claim] = timegm(
                    payload[time_claim].utctimetuple())  # type: ignore

        json_payload = json.dumps(
            payload,
            separators=(',', ':'),
            cls=json_encoder
        )

        return super(PyJWT, self).encode(
            fernet_crypt(json_payload, password, salt),
            key,
            algorithm,
            headers,
            json_encoder
        )

    def decode(self,
               jwt: str,
               key: str = '',
               verify: bool = True,
               algorithms: List[str] = None,
               options: Dict = None,
               **kwargs):
        """
        :type encrypt_password: str
        :type encrypt_salt: str
        """
        if verify and not algorithms:
            warnings.warn(
                'It is strongly recommended that you pass in a ' +
                'value for the "algorithms" argument when calling decode(). ' +
                'This argument will be mandatory in a future version.',
                DeprecationWarning
            )

        password = kwargs.get("encrypt_password", None)
        if not password:
            raise ValueError("Invalid encrypt password")
        salt = kwargs.get("encrypt_salt", None)

        crypt_payload, _, _, _ = self._load(jwt)

        payload = fernet_decrypt(crypt_payload, password, salt).decode("UTF-8")

        if options is None:
            options = {'verify_signature': verify}
        else:
            options.setdefault('verify_signature', verify)

        try:
            payload = json.loads(payload)
        except ValueError as e:
            raise DecodeError('Invalid payload string: %s' % e)
        if not isinstance(payload, Mapping):
            raise DecodeError('Invalid payload string: must be a json object')

        if verify:
            merged_options = merge_dict(self.options, options)
            self._validate_claims(payload, merged_options, **kwargs)

        return payload


_new_obj = PyJWTPayloadEncrypt()
jwt.api_jwt.encode = PyJWTPayloadEncrypt.encode
jwt.api_jwt.decode = PyJWTPayloadEncrypt.decode
jwt.encode = _new_obj.encode
jwt.decode = _new_obj.decode


class AuthenticationEncrypted(Authentication):

    def __init__(self, app, config):
        super().__init__(app, config)

        self.encrypt_password = app.config.get("ENCRYPT_PASSWORD", None)
        self.encrypt_salt = app.config.get("ENCRYPT_SALT", None)
        self.full_user_info = app.config.get("FULL_USER_INFO", False)

        if not self.encrypt_password:
            raise ValueError("Password not defined! Please set "
                             "'ENCRYPT_PASSWORD'")

    def _decode(self, token, verify=True, inline_claims=None):
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
            encrypt_password=self.encrypt_password,
            encrypt_salt=self.encrypt_salt,
            **kwargs,
        )

        if verify:
            if self._extra_verifications:
                self._verify_extras(decoded)
            if self._custom_claims or inline_claims:
                self._verify_custom_claims(
                    decoded, inline_claims=inline_claims
                )

        return decoded

    async def generate_access_token(
            self, user, extend_payload=None, custom_claims=None
    ):
        """
        Generate an access token for a given user.
        """
        payload = await self._get_payload(user, inline_claims=custom_claims)
        secret = self._get_secret(True)
        algorithm = self._get_algorithm()

        # Payload
        for time_claim in ['exp', 'iat', 'nbf']:
            # Convert datetime to a intDate value in known time-format claims
            if isinstance(payload.get(time_claim), datetime):
                payload[time_claim] = timegm(
                    payload[time_claim].utctimetuple())  # ty

        if extend_payload:
            payload = await utils.call(
                extend_payload, payload=payload, user=user
            )

        return jwt.encode(payload,
                          secret,
                          algorithm=algorithm,
                          encrypt_password=self.encrypt_password,
                          encrypt_salt=self.encrypt_salt).decode("utf-8")

    async def _get_payload(self, user, inline_claims=None):
        payload = await super(AuthenticationEncrypted, self)._get_payload(
            user,
            inline_claims
        )

        if self.full_user_info:
            if hasattr(user, "to_dict"):
                payload.update(user.to_dict())
            else:
                payload.update(user)

        return payload