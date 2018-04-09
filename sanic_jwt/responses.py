from sanic.response import json
from .base import BaseDerivative


class Responses(BaseDerivative):
    @staticmethod
    async def get_access_token_output(request, user, config, instance):
        access_token = await instance.auth.get_access_token(user)

        output = {config.get('access_token_name', request=request, user=user): access_token}

        return access_token, output

    @staticmethod
    def get_token_reponse(request,
                          access_token,
                          output,
                          config,
                          refresh_token=None):
        response = json(output)

        if config.get('cookie_set', request=request):
            key = config.get('cookie_access_token_name', request=request)
            response.cookies[key] = access_token
            response.cookies[key]['domain'] = \
                config.get('cookie_domain', request=request)
            response.cookies[key]['httponly'] = \
                config.get('cookie_httponly', request=request)

            if refresh_token and \
                    config.get('refresh_token_enabled', request=request):
                key = config.cookie_refresh_token_name
                response.cookies[key] = refresh_token
                response.cookies[key]['domain'] = \
                    config.get('cookie_domain', request=request)
                response.cookies[key]['httponly'] = \
                    config.get('cookie_httponly', request=request)

        return response

    @staticmethod
    def extend_authenticate(request,
                            user=None,
                            access_token=None,
                            refresh_token=None):
        return {}

    @staticmethod
    def extend_retrieve_user(request, user=None, payload=None):
        return {}

    @staticmethod
    def extend_verify(request, user=None, payload=None):
        return {}

    @staticmethod
    def extend_refresh(request,
                       user=None,
                       access_token=None,
                       refresh_token=None,
                       purported_token=None,
                       payload=None):
        return {}

    @staticmethod
    def exception_response(request, exception):
        return json({
            'reasons': exception.args[0],
            'exception': exception.__class__.__name__
        }, status=exception.status_code)
