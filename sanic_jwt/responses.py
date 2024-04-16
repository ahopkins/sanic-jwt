from typing import Optional

from sanic.response import json
from sanic import HTTPResponse

from .base import BaseDerivative

def _set_cookie(response : HTTPResponse, key : str, value : str, config, force_httponly : Optional[bool] = None):
    response.cookies.add_cookie(
        key=key,
        value=value,
        httponly=config.cookie_httponly() if force_httponly is None else force_httponly,
        path=config.cookie_path(),
        domain=config.cookie_domain() or None, # cookie_domain() may be '' (empty string)
        expires=config.cookie_expires() or None, # cookie_expires() may be `0`
        max_age=config.cookie_max_age() or None,
        samesite=config.cookie_samesite() or "Lax",
        secure=is_secure if (is_secure := config.cookie_secure()) is not None else True
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
