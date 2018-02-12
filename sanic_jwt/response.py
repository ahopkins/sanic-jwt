import importlib
from sanic.response import json


class Response:
    @staticmethod
    async def get_access_token_output(request, user, config):
        access_token = await request.app.auth.get_access_token(user)

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
            response.cookies[key] = str(access_token, 'utf-8')
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

    def extend_authenticate(self,
                            request,
                            user=None,
                            access_token=None,
                            refresh_token=None):
        return {}

    def extend_retrieve_user(self, request, user=None, payload=None):
        return {}

    def extend_verify(self, request, user=None, payload=None):
        return {}

    def extend_refresh(self,
                       request,
                       user=None,
                       access_token=None,
                       refresh_token=None,
                       purported_token=None,
                       payload=None):
        return {}


def make_response(r):
    # TODO:
    # - Find a better solution to assigning to the module's response attribute
    module = importlib.import_module('sanic_jwt.endpoints')
    if module.response is None:
        setattr(module, 'response', r)
