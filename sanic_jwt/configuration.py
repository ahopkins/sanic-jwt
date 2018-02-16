import copy
import logging

from . import exceptions
from . import utils


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
    'leeway': 60 * 3,
    'refresh_token_enabled': False,
    'refresh_token_name': 'refresh_token',
    'path_to_authenticate': '/',
    'path_to_retrieve_user': '/me',
    'path_to_verify': '/verify',
    'path_to_refresh': '/refresh',
    'scopes_enabled': False,
    'scopes_name': 'scopes',
    'secret': 'This is a big secret. Shhhhh',
    'private_key': None,
    'strict_slashes': False,
    'url_prefix': '/auth',
    'user_id': 'user_id',
    'verify_exp': True,
}

aliases = {
    'public_key': 'secret',
}


config = None


class Configuration:
    def __init__(self, app_config, **kwargs):
        presets = self.extract_presets(app_config)
        self.kwargs = self._merge_aliases(kwargs)
        self.defaults = copy.deepcopy(defaults)
        self.defaults.update(self._merge_aliases(presets))
        self.defaults.update(self.kwargs)

        list(map(self.__map_config, self.defaults.items()))
        self._validate_keys()

    def __map_config(self, config_item):
        key, value = config_item
        if (not hasattr(self, key) or key in self.kwargs):
            setattr(self, key, value)

    def __iter__(self):
        return ((x, getattr(self, x)) for x in self.defaults.keys())  # noqa

    def __repr__(self):
        return str(dict(iter(self)))  # noqa

    def _validate_keys(self):
        logging.getLogger(__name__).debug('validating provided secret(s)')
        if utils.algorithm_is_asymmetric(self.algorithm) and \
                self.private_key is None:
            raise exceptions.RequiredKeysNotFound

    @staticmethod
    def extract_presets(app_config):
        """
        Pull the application's configurations for Sanic JWT
        """
        return {
            x.lower()[10:]: app_config.get(x)
            for x in filter(lambda x: x.startswith('SANIC_JWT'), app_config)
        }

    @staticmethod
    def _merge_aliases(config):
        popped = {}
        for k in aliases.keys():
            if k in config:
                popped[aliases[k]] = config.pop(k)
        config.update(popped)
        return config
