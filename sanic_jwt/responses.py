from sanic.response import json
from sanic import HTTPResponse

from .base import BaseDerivative

def _set_cookie(response : HTTPResponse, key : str, value : str, config, force_httponly : bool = None):
    def value_or(val, def_val):
        return val if val is not None else def_val

    response.cookies.add_cookie(
        key=key,
        value=value,
        httponly=config.cookie_httponly() if force_httponly is None else force_httponly,
        path=config.cookie_path(),
        domain=value_or(config.cookie_domain(), None),
        expires=value_or(config.cookie_expires(), None),
        max_age=value_or(config.cookie_max_age(), None),
        samesite=value_or(config.cookie_samesite(), "Lax"),
        secure=value_or(config.cookie_secure(), True)
    )

class Responses(BaseDerivative):
    @staticmethod
    async def get_access_token_output(request, user, config, instance):
        access_token = await instance.ctx.auth.generate_access_token(user)

        output = {config.access_token_name(): access_token}

        return access_token, output

    @staticmethod
    def get_token_response(
        request, access_token, output, config, refresh_token=None
    ):
        response = json(output)

        if config.cookie_set():
            key = config.cookie_access_token_name()

            if config.cookie_split():
                signature_name = config.cookie_split_signature_name()
                header_payload, signature = access_token.rsplit(
                    ".", maxsplit=1
                )
                _set_cookie(
                    response, key, header_payload, config, force_httponly=False
                )
                _set_cookie(
                    response,
                    signature_name,
                    signature,
                    config,
                    force_httponly=True,
                )
            else:
                _set_cookie(response, key, access_token, config)

            if refresh_token and config.refresh_token_enabled():
                key = config.cookie_refresh_token_name()
                _set_cookie(response, key, refresh_token, config)

        return response

    @staticmethod
    def extend_authenticate(
        request, user=None, access_token=None, refresh_token=None
    ):
        return {}

    @staticmethod
    def extend_retrieve_user(request, user=None, payload=None):
        return {}

    @staticmethod
    def extend_verify(request, user=None, payload=None):
        return {}

    @staticmethod
    def extend_refresh(
        request,
        user=None,
        access_token=None,
        refresh_token=None,
        purported_token=None,
        payload=None,
    ):
        return {}

    @staticmethod
    def exception_response(request, exception):
        reasons = (
            exception.args[0]
            if isinstance(exception.args[0], list)
            else [exception.args[0]]
        )
        return json(
            {"reasons": reasons, "exception": exception.__class__.__name__},
            status=exception.status_code,
        )
