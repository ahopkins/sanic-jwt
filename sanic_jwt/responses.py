from sanic.response import json
from .base import BaseDerivative


class Responses(BaseDerivative):
    async def get_access_token_output(self, request, user, config):
        instance = request.app if hasattr(request.app, 'auth') \
            else self.instance
        access_token = await instance.auth.get_access_token(user)

        output = {config.access_token_name: access_token}

        return access_token, output

    @staticmethod
    def get_token_reponse(request,
                          access_token,
                          output,
                          config,
                          refresh_token=None):
        response = json(output)

        if config.cookie_set:
            key = config.cookie_access_token_name
            response.cookies[key] = access_token
            response.cookies[key]['domain'] = \
                config.cookie_domain
            response.cookies[key]['httponly'] = \
                config.cookie_httponly

            if refresh_token and \
                    config.refresh_token_enabled:
                key = config.cookie_refresh_token_name
                response.cookies[key] = refresh_token
                response.cookies[key]['domain'] = \
                    config.cookie_domain
                response.cookies[key]['httponly'] = \
                    config.cookie_httponly

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
            'exception': str(exception)
        }, status=exception.status_code)
