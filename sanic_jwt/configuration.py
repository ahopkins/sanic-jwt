import asyncio
import copy
import logging

from . import exceptions
from . import utils
from .cache import get_cached
from .cache import is_cached
from .cache import to_cache


defaults = {
    "access_token_name": "access_token",
    "algorithm": "HS256",
    "auth_mode": True,
    "authorization_header": "authorization",
    "authorization_header_prefix": "Bearer",
    "authorization_header_refresh_prefix": "Refresh",
    "claim_aud": None,
    "claim_iat": False,
    "claim_iss": None,
    "claim_nbf": False,
    "claim_nbf_delta": 0,
    "cookie_access_token_name": "access_token",
    "cookie_domain": "",
    "cookie_httponly": True,
    "cookie_refresh_token_name": "refresh_token",
    "cookie_set": False,
    "cookie_strict": True,
    "debug": False,
    "do_protection": True,
    "expiration_delta": 60 * 5 * 6,
    "generate_refresh_token": utils.generate_token,
    "leeway": 60 * 3,
    "login_redirect_url": "/index.html",
    "path_to_authenticate": "/",
    "path_to_refresh": "/refresh",
    "path_to_retrieve_user": "/me",
    "path_to_verify": "/verify",
    "private_key": None,
    "query_string_access_token_name": "access_token",
    "query_string_refresh_token_name": "refresh_token",
    "query_string_set": False,
    "query_string_strict": True,
    "refresh_token_enabled": False,
    "refresh_token_name": "refresh_token",
    "scopes_enabled": False,
    "scopes_name": "scopes",
    "secret": "This is a big secret. Shhhhh",
    "strict_slashes": False,
    "url_prefix": "/auth",
    "user_id": "user_id",
    "blueprint_name": "auth_bp",
    "verify_exp": True,
    "login_redirect_url": None,
}

aliases = {
    "cookie_access_token_name": "cookie_token_name",
    "secret": "public_key",
}

ignore_keys = (
    "add_scopes_to_payload",
    "authenticate",
    "class_views",
    "extend_payload",
    "retrieve_refresh_token",
    "retrieve_user",
    "store_refresh_token",
    "destructure_scopes",
)

logger = logging.getLogger(__name__)


def _warn_key(key):
    if key not in ignore_keys:
        logger.warning(
            "Configuration key '%s' found is not valid for sanic-jwt", key
        )


def _create_or_overwrite_config_item(value, key, item_aliases, instance):
    setattr(
        instance,
        key,
        ConfigItem(
            value, item_name=key, config=instance, aliases=item_aliases
        ),
    )


def _update_config_item(key, item_aliases, instance):
    getattr(instance, key)._item_name = key
    getattr(instance, key)._aliases = item_aliases
    getattr(instance, key)._config = instance


class ConfigItem:
    def __init__(
        self,
        value,
        item_name=None,
        config=None,
        inject_request=True,
        aliases=None,
    ):
        self._value = value
        self._item_name = item_name
        self._config = config
        self._inject_request = inject_request

        if aliases is not None and isinstance(aliases, (list, tuple, set)):
            self._aliases = aliases
        else:
            self._aliases = []

    def update(self, value):
        self._value = value

    def __call__(self, **kwargs):
        if asyncio.get_event_loop().is_running():
            if is_cached(self._item_name):
                return get_cached(self._item_name)

            if self._get_from_config is not None:
                args = []

                if self._inject_request and is_cached("_request"):  # noqa
                    args.append(get_cached("_request"))
                val = self._get_from_config.__call__(*args)
                to_cache(self._item_name, val)
                return val

        return self._value

    @property
    def _get_from_config(self):
        if hasattr(self._config, self._get_fn):
            return getattr(self._config, self._get_fn)

        return None

    @property
    def _get_fn(self):
        return "get_{}".format(self._item_name)

    @property
    def aliases(self):
        return self._aliases


class Configuration:
    def __iter__(self):  # noqa
        for key in self.config_keys:
            yield getattr(self, key)

        for key in self.aliases_keys:
            yield getattr(self, key)

    def __contains__(self, item):
        return item in self.all_config_keys

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)

        _defaults = copy.deepcopy(defaults)
        _aliases = copy.deepcopy(aliases)
        _config_keys = []

        if args and isinstance(args[0], dict):  # noqa
            _args = cls.extract_presets(args[0])
            for key, value in _args.items():
                if key in _defaults or key in _aliases:
                    _defaults.update({key: value})

        for key, value in _defaults.items():
            item_aliases = []
            if key in _aliases:
                item_aliases = [aliases.get(key)]

            # check if a configuration key is set
            # and is an instance of ConfigItem
            if hasattr(instance, key) and isinstance(
                getattr(instance, key), ConfigItem
            ):
                _update_config_item(key, item_aliases, instance)
            # check if a configuration key is set with a value
            elif hasattr(instance, key):
                val = getattr(instance, key)
                _create_or_overwrite_config_item(
                    val, key, item_aliases, instance
                )
            else:
                _create_or_overwrite_config_item(
                    value, key, item_aliases, instance
                )

            # check if a setter is available on config class
            fn_name = "set_{}".format(key)
            if hasattr(instance, fn_name):
                set_fn = getattr(instance, fn_name)
                if not callable(set_fn):
                    logger.warning(
                        'variable "%s" set in Configuration is not callable',
                        fn_name,
                    )
                    continue

                val = set_fn.__call__()
                if isinstance(val, ConfigItem):
                    setattr(instance, key, val)
                    _update_config_item(key, item_aliases, instance)
                else:
                    _create_or_overwrite_config_item(
                        val, key, item_aliases, instance
                    )

            # 'reference' aliases
            for alias in item_aliases:
                setattr(instance, alias, getattr(instance, key))

            _config_keys.append(key)

        setattr(instance, "_config_keys", _config_keys)
        setattr(instance, "_config_aliases", _aliases)
        setattr(instance, "_config_aliases_keys", _aliases.values())
        setattr(
            instance,
            "_all_config_keys",
            _config_keys + list(_aliases.values()),
        )

        return instance

    def get(self, item):
        """Helper method to avoid calling getattr
        """
        if item in self:  # noqa
            item = getattr(self, item)
            return item()

    @property
    def config_keys(self):
        return self._config_keys

    @property
    def config_aliases(self):
        return self._config_aliases

    @property
    def all_config_keys(self):
        return self._all_config_keys

    @property
    def config_aliases_keys(self):
        return self._config_aliases_keys

    def __init__(self, app_config, **kwargs):
        for key, value in kwargs.items():
            self._merge(key, value)

        self._validate_secret()
        self._validate_keys()
        self._load_keys()

    def _merge(self, key, value):
        if key in self.config_keys:
            item = getattr(self, key)
            item.update(value)
            for alias in item.aliases:
                self._merge(alias, value)
        elif key in self.config_aliases_keys:
            correct_key = None
            for v in self.config_aliases.values():  # noqa
                if key == v:
                    correct_key = key
                    break

            if hasattr(self, correct_key):  # noqa
                getattr(self, correct_key).update(value)
        else:
            _warn_key(key)

    def _validate_secret(self):
        logger.debug("validating provided secret")
        if self.secret() is None or (
            isinstance(self.secret(), str) and self.secret().strip() == ""
        ):
            raise exceptions.InvalidConfiguration(
                "the SANIC_JWT_SECRET parameter cannot be None nor an empty "
                "string"
            )

    def _validate_keys(self):
        logger.debug("validating keys (if needed)")
        if utils.algorithm_is_asymmetric(self.algorithm()) and (
            self.private_key() is None
            or (
                isinstance(self.private_key(), str)
                and self.private_key().strip() == ""
            )
        ):
            raise exceptions.RequiredKeysNotFound

    def _load_keys(self):
        logger.debug("loading secret and/or keys (if needed)")
        try:
            self.secret.update(utils.load_file_or_str(self.secret()))
            if utils.algorithm_is_asymmetric(self.algorithm()):
                self.private_key.update(
                    utils.load_file_or_str(self.private_key())
                )
        except exceptions.ProvidedPathNotFound as exc:
            if utils.algorithm_is_asymmetric(self.algorithm()):
                raise exceptions.RequiredKeysNotFound

            raise exc  # noqa

    @staticmethod
    def extract_presets(app_config):
        """
        Pull the application's configurations for Sanic JWT
        """
        return {
            x.lower()[10:]: app_config.get(x)
            for x in filter(lambda x: x.startswith("SANIC_JWT"), app_config)
        }
