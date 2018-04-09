import copy
import logging
from abc import ABC, abstractmethod

from . import exceptions, utils
from .cache import get_value, has_value, set_value


defaults = {
    'access_token_name': 'access_token',
    'algorithm': 'HS256',
    'authorization_header': 'authorization',
    'authorization_header_prefix': 'Bearer',
    'authorization_header_refresh_prefix': 'Refresh',
    'claim_aud': None,
    'claim_iat': False,
    'claim_iss': None,
    'claim_nbf': False,
    'claim_nbf_delta': 0,
    'cookie_domain': '',
    'cookie_httponly': True,
    'cookie_refresh_token_name': 'refresh_token',
    'cookie_set': False,
    'cookie_strict': True,
    'cookie_access_token_name': 'access_token',
    'debug': False,
    'expiration_delta': 60 * 5 * 6,
    'generate_refresh_token': utils.generate_token,
    'leeway': 60 * 3,
    'refresh_token_enabled': False,
    'refresh_token_name': 'refresh_token',
    'path_to_authenticate': '/',
    'path_to_retrieve_user': '/me',
    'path_to_verify': '/verify',
    'path_to_refresh': '/refresh',
    'private_key': None,
    'scopes_enabled': False,
    'scopes_name': 'scopes',
    'secret': 'This is a big secret. Shhhhh',
    'strict_slashes': False,  # not dynamic (no request, no user)
    'url_prefix': '/auth',  # not dynamic (no request, no user)
    'user_id': 'user_id',
    'verify_exp': True,
}

aliases = {
    'cookie_token_name': 'cookie_access_token_name',
    'public_key': 'secret',
}

logger = logging.getLogger(__name__)
config = None


class BaseConfiguration(ABC):
    @abstractmethod
    def get(self, key, *, request=None, user=None, **kwargs):
        pass  # noqa

    @abstractmethod
    def set(self, key, value, *, request=None, user=None, transient=True, **kwargs):
        pass  # noqa

    @abstractmethod
    def has(self, key):
        pass  # noqa

    @property
    def inside_context(self):
        if hasattr(self, '_inside_context'):
            return self._inside_context
        return False

    @inside_context.setter
    def inside_context(self, value):
        if not hasattr(self, '_inside_context'):
            setattr(self, '_inside_context', value)
        else:
            self._inside_context = value

    # def __getattribute__(self, item):
    #     print('>>> getattribute {}'.format(item))
    #     return super().__getattribute__(item)

    # def __getattr__(self, item):
    #     print('>>> getattr {}'.format(item))
    #     return super().__getattr__(item)


class Configuration(BaseConfiguration):
    def __init__(self, app_config, **kwargs):
        presets = self.extract_presets(app_config)
        self.kwargs = self._merge_aliases(kwargs)
        self.defaults = copy.deepcopy(defaults)
        self.defaults.update(self._merge_aliases(presets))
        self.defaults.update(self.kwargs)

        list(map(self.__map_config, self.defaults.items()))
        self._validate_secret()
        self._validate_keys()
        self._load_keys()

    def get(self, key, *, request=None, user=None, transient=False, default=None, **kwargs):
        v = None
        if self.inside_context or transient:
            v = get_value(key)
        if v is None:
            v = getattr(self, key)
        if default and v is None:
            return default
        return v

    def set(self, key, value, *, request=None, user=None, transient=True, **kwargs):
        if self.inside_context or transient:
            set_value(key, value)
        else:
            setattr(self, key, value)
            self.defaults.update({key: value})

    def has(self, key, transient=False):
        key_exists = False
        if self.inside_context or transient:
            key_exists = key_exists or has_value(key)
        return key_exists or hasattr(self, key) or key in self.defaults

    def __map_config(self, config_item):
        key, value = config_item
        if (not hasattr(self, key) or key in self.kwargs):
            setter_name = 'set_{}'.format(key)
            if hasattr(self, setter_name):
                value = getattr(self, setter_name)()
            setattr(self, key, value)

    def __iter__(self):
        return ((x, getattr(self, x)) for x in self.defaults.keys())  # noqa

    def __repr__(self):
        return str(dict(iter(self)))  # noqa

    def _validate_secret(self):
        logger.debug('validating provided secret')
        if self.secret is None or (
                isinstance(self.secret, str) and self.secret.strip() == ''):
            raise exceptions.InvalidConfiguration(
                'the SANIC_JWT_SECRET parameter cannot be None nor an empty '
                'string')

    def _validate_keys(self):
        logger.debug('validating keys (if needed)')
        if utils.algorithm_is_asymmetric(self.algorithm) and (
            self.private_key is None or (
                isinstance(self.private_key, str) and
                self.private_key.strip() == ''
            )
        ):
            raise exceptions.RequiredKeysNotFound

    def _load_keys(self):
        logger.debug('loading secret and/or keys (if needed)')
        try:
            self.secret = utils.load_file_or_str(self.secret)
            self.defaults.update({'secret': self.secret})
            if utils.algorithm_is_asymmetric(self.algorithm):
                self.private_key = utils.load_file_or_str(self.private_key)
                self.defaults.update({'private_key': self.private_key})
        except exceptions.ProvidedPathNotFound as exc:
            if utils.algorithm_is_asymmetric(self.algorithm):
                raise exceptions.RequiredKeysNotFound
            raise exc

    @staticmethod
    def _merge_aliases(config):
        popped = {}
        for k in aliases.keys():
            if k in config:
                popped[aliases[k]] = config.pop(k)
        config.update(popped)
        return config

    @staticmethod
    def extract_presets(app_config):
        """
        Pull the application's configurations for Sanic JWT
        """
        return {
            x.lower()[10:]: app_config.get(x)
            for x in filter(lambda x: x.startswith('SANIC_JWT'), app_config)
        }


# class _MetaConfiguration(type):

#     def __new__(cls, name, bases, namespace, **kw):
#         print('-------------------------')
#         print('name')
#         print(name)
#         print('bases')
#         print(bases)
#         print('namespace')
#         print(namespace)
#         print('kw')
#         print(kw)
#         print('')
#         return super().__new__(cls, name, bases, namespace)

#     # def __instancecheck__(self, instance):
#     #     pass

#     # def __subclasscheck__(self, subclass):
#     #     pass

#     def __getattribute__(*args):
#         print("Metaclass getattribute invoked")
#         print(args)
#         return type.__getattribute__(*args)


class DynamicConfiguration(Configuration):
    def __init__(self, app_config, **kwargs):
        # presets = self.extract_presets(app_config)
        # self.kwargs = self._merge_aliases(kwargs)
        # self.defaults = copy.deepcopy(defaults)
        # self.defaults.update(self._merge_aliases(presets))
        # self.defaults.update(self.kwargs)

        # list(map(self.__map_config, self.defaults.items()))
        # self._validate_secret()
        # self._validate_keys()
        # self._load_keys()
        pass

    async def get(self, key, *, request=None, user=None, transient=False, **kwargs):
        # v = None
        # if transient:
        #     v = get_value(key)
        # if v is None:
        #     v = getattr(self, key)
        # return v
        pass

    async def set(self, key, value, *, request=None, user=None, transient=True, **kwargs):
        # if transient:
        #     set_value(key, value)
        # else:
        #     setattr(self, key, value)
        #     self.defaults.update({key: value})
        pass
