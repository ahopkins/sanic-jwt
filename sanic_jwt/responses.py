from sanic.response import json

from .base import BaseDerivative

COOKIE_OPTIONS = (
    ("domain", "cookie_domain"),
    ("expires", "cookie_expires"),
    ("max-age", "cookie_max_age"),
    ("samesite", "cookie_samesite"),
    ("secure", "cookie_secure"),
)


def _set_cookie(response, key, value, config, force_httponly=None):
    response.cookies[key] = value
    response.cookies[key]["httponly"] = (
        config.cookie_httponly() if force_httponly is None else force_httponly
    )
    response.cookies[key]["path"] = config.cookie_path()

    for item, option in COOKIE_OPTIONS:
        value = getattr(config, option)()
        if value:
            response.cookies[key][item] = value


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
