import importlib


defaults = {
    'access_token_name': 'access_token',
    'algorithm': 'HS256',
    'authorization_header': 'authorization',
    'authorization_header_prefix': 'Bearer',
    'authorization_header_refresh_prefix': 'Refresh',
    'claim_aud': None,  # String
    'claim_iat': None,  # Boolean
    'claim_iss': None,  # String
    'claim_nbf': None,  # Boolean
    'claim_nbf_delta': 0,
    'cookie_domain': '',
    'cookie_httponly': True,
    'cookie_refresh_token_name': 'refresh_token',
    'cookie_set': False,
    'cookie_strict': True,
    'cookie_access_token_name': 'access_token',
    'debug': False,
    'expiration_delta': 60 * 5 * 6,
    'handler_payload': 'sanic_jwt.handlers.build_payload',
    'handler_payload_extend': 'sanic_jwt.handlers.extend_payload',
    'handler_payload_scopes': None,
    'leeway': 60 * 3,
    'refresh_token_enabled': False,
    'refresh_token_name': 'refresh_token',
    'scopes_name': 'scopes',
    'secret': 'This is a big secret. Shhhhh',
    'strict_slashes': False,
    'url_prefix': '/auth',
    'user_id': 'user_id',
    'verify_exp': True,
}


config = None


class Configuration(object):
    def __init__(self, app_config, **kwargs):
        presets = self.extract_presets(app_config)
        self.kwargs = kwargs
        defaults.update(presets)
        defaults.update(kwargs)

        # TODO:
        # - limit to enumerated settings, and raise InvalidConfiguration(e)
        list(map(self.__map_config, defaults.items()))

        config = self

    def __map_config(self, config_item):
        key, value = config_item
        if not hasattr(self, key) or key in self.kwargs:
            setattr(self, key, value)

    def __iter__(self):
        return ((x, getattr(self, x)) for x in defaults.keys())

    @staticmethod
    def extract_presets(app_config):
        """
        Pull the application's configurations for Sanic JWT
        """
        return {
            x.lower()[10:]: app_config.get(x)
            for x in filter(lambda x: x.startswith('SANIC_JWT'), app_config)
        }




def make_config(c):
    # TODO:
    # - Find a better solution to assigning to the module's config attribute
    module = importlib.import_module('sanic_jwt.configuration')
    if module.config is None:
        setattr(module, 'config', c)
    # else:
    #     raise AttributeError('Cannot make_config on an existing config instance.')


def get_config():
    return config
