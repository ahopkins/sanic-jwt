import inspect

from collections import namedtuple

from sanic import Blueprint
from sanic import Sanic

from sanic_jwt import endpoints
from sanic_jwt import exceptions
from sanic_jwt.authentication import Authentication
from sanic_jwt.configuration import Configuration
from sanic_jwt.decorators import inject_user
from sanic_jwt.decorators import protected
from sanic_jwt.decorators import scoped
from sanic_jwt.responses import Responses

_Handler = namedtuple(
    "_Handler", ["name", "keys", "exception", "outside_auth_mode"]
)
_EndpointMapping = namedtuple(
    "_EndpointMapping", ["cls", "endpoint", "keys", "is_protected"]
)


def initialize(*args, **kwargs):
    """
    Functional approach to initializing Sanic JWT. This was the original
    method, but was replaced by the Initialize class. It is recommended to use
    the class because it is more flexible. There is no current plan to remove
    this method, but it may be depracated in the future.
    """
    if len(args) > 1:
        kwargs.update({"authenticate": args[1]})
    return Initialize(args[0], **kwargs)


endpoint_mappings = (
    _EndpointMapping(
        endpoints.AuthenticateEndpoint, "authenticate", ["auth_mode"], False
    ),
    _EndpointMapping(
        endpoints.RetrieveUserEndpoint, "retrieve_user", ["auth_mode"], True
    ),
    _EndpointMapping(endpoints.VerifyEndpoint, "verify", ["auth_mode"], False),
    _EndpointMapping(
        endpoints.RefreshEndpoint,
        "refresh",
        ["auth_mode", "refresh_token_enabled"],
        False,
    ),
)

auth_mode_handlers = (
    _Handler(
        "authenticate", None, exceptions.AuthenticateNotImplemented(), False
    ),
    _Handler(
        "store_refresh_token",
        ["refresh_token_enabled"],
        exceptions.RefreshTokenNotImplemented(),
        False,
    ),
    _Handler(
        "retrieve_refresh_token",
        ["refresh_token_enabled"],
        exceptions.RefreshTokenNotImplemented(),
        False,
    ),
    _Handler(
        "add_scopes_to_payload",
        ["scopes_enabled"],
        exceptions.ScopesNotImplemented(),
        False,
    ),
    _Handler("override_scope_validator", None, None, False),
    _Handler("destructure_scopes", None, None, False),
    _Handler("extend_payload", None, None, False),
)
auth_mode_agnostic_handlers = (_Handler("retrieve_user", None, None, True),)
handlers = auth_mode_handlers + auth_mode_agnostic_handlers

init_classes = (
    "configuration_class",
    "authentication_class",
    "responses_class",
)


class Initialize:
    """Class used to initialize Sanic JWT

    Must be initialized with a keyword argument: `authenticate` that is a
    method that MUST return a user object that when iterated upon returns a
    dictionary, or has a `to_dict` method. The resulting dictionary MUST
    have a key/value for a unique user id.
    """

    authentication_class = Authentication
    configuration_class = Configuration
    responses_class = Responses

    def __init__(self, instance, app=None, **kwargs):
        for class_name in init_classes:
            if class_name in kwargs:
                value = kwargs.pop(class_name)
                setattr(self, class_name, value)

        app = self.__get_app(instance, app=app)

        self.app = app
        self.kwargs = kwargs
        self.instance = instance
        self.config = None
        self.bp = None

        self.__check_deprecated()
        self.__check_classes()
        self.__load_configuration()
        self.__initialize_bp()
        self.__load_responses()
        self.__add_class_views()
        self.__add_endpoints()
        self.__initialize_instance()
        self.__initialize_claims()

    def __check_deprecated(self):
        """
        Checks for deprecated configuration keys
        """
        # Depracation notices
        if "SANIC_JWT_HANDLER_PAYLOAD_SCOPES" in self.app.config:
            raise exceptions.InvalidConfiguration(
                "SANIC_JWT_HANDLER_PAYLOAD_SCOPES has been deprecated. "
                "Instead, pass your handler method (not an import path) as "
                "initialize(add_scopes_to_payload=my_scope_extender)"
            )

        if "SANIC_JWT_PAYLOAD_HANDLER" in self.app.config:
            raise exceptions.InvalidConfiguration(
                "SANIC_JWT_PAYLOAD_HANDLER has been deprecated. "
                "Instead, you will need to subclass Authentication. "
            )

        if "SANIC_JWT_HANDLER_PAYLOAD_EXTEND" in self.app.config:
            raise exceptions.InvalidConfiguration(
                "SANIC_JWT_HANDLER_PAYLOAD_EXTEND has been deprecated. "
                "Instead, you will need to subclass Authentication. "
                "Check out the documentation for more information."
            )

    def __add_endpoints(self):
        """
        Initialize the Sanic JWT Blueprint and add to the instance initialized
        """
        for mapping in endpoint_mappings:
            if all(map(self.config.get, mapping.keys)):
                self.__add_single_endpoint(
                    mapping.cls, mapping.endpoint, mapping.is_protected
                )

        self.bp.exception(exceptions.SanicJWTException)(
            self.responses.exception_response
        )

        if not self.instance_is_blueprint:
            url_prefix = self._get_url_prefix()
            self.instance.blueprint(self.bp, url_prefix=url_prefix)

    def __add_class_views(self):
        """
        Include any custom class views on the Sanic JWT Blueprint
        """
        config = self.config
        if "class_views" in self.kwargs:
            class_views = self.kwargs.pop("class_views")

            for route, view in class_views:
                if issubclass(view, endpoints.BaseEndpoint) and isinstance(
                    route, str
                ):
                    self.bp.add_route(
                        view.as_view(
                            self.responses,
                            config=self.config,
                            instance=self.instance,
                        ),
                        route,
                        strict_slashes=config.strict_slashes(),
                    )
                else:
                    raise exceptions.InvalidClassViewsFormat()

    def __check_classes(self):
        """
        Check if any of the default classes (`Authentication`, `Configuration`
        and / or `Responses`) have been overwitten and if they're still valid
        """
        # msg took from BaseAuthentication
        msg = (
            "Sanic JWT was not initialized properly. It did not received "
            "an instance of {}"
        )
        if not issubclass(self.authentication_class, Authentication):
            raise exceptions.InitializationFailure(
                message=msg.format("Authentication")
            )

        if not issubclass(self.configuration_class, Configuration):
            raise exceptions.InitializationFailure(
                message=msg.format("Configuration")
            )

        if not issubclass(self.responses_class, Responses):
            raise exceptions.InitializationFailure(
                message=msg.format("Responses")
            )

    def __initialize_instance(self):
        """
        Take any predefined methods/handlers and insert them into Sanic JWT
        """
        config = self.config

        # Initialize instance of the Authentication class
        self.instance.auth = self.authentication_class(self.app, config=config)

        init_handlers = (
            handlers if config.auth_mode() else auth_mode_agnostic_handlers
        )

        for handler in init_handlers:
            if handler.keys is None:
                self.__check_method_in_auth(handler.name, handler.exception)
            else:
                if all(map(config.get, handler.keys)):
                    self.__check_method_in_auth(
                        handler.name, handler.exception
                    )

        for handler in init_handlers:
            if handler.name in self.kwargs:
                method = self.kwargs.pop(handler.name)
                setattr(self.instance.auth, handler.name, method)

    def __initialize_claims(self):
        if "extra_verifications" in self.kwargs:
            self.instance.auth._extra_verifications = self.kwargs.get(
                "extra_verifications"
            )

        if "custom_claims" in self.kwargs:
            try:
                for claim in self.kwargs.get("custom_claims"):
                    claim._register(self)
            except AttributeError:
                raise exceptions.InvalidCustomClaim

    def __check_method_in_auth(self, method_name, exc):
        if method_name not in self.kwargs:
            method_impl = getattr(self.instance.auth, method_name)
            if not inspect.ismethod(method_impl):
                self.__raise_if_not_none(exc)
            if method_impl.__func__ == getattr(Authentication, method_name):
                self.__raise_if_not_none(exc)

            self.kwargs.update({method_name: method_impl})

    def __load_configuration(self):
        """
        Configure settings for the instance in the following order:

        1. Sanic JWT's defaults
        2. Custom Configuration class
        3. Key word arguments passed to Initialize
        """
        handler_to_enable = filter(lambda h: h.keys is not None, handlers)
        for handler in handler_to_enable:
            if handler.name in self.kwargs:
                for k in handler.keys:
                    self.kwargs.update({k: True})

        self.config = self.configuration_class(self.app.config, **self.kwargs)

    def __load_responses(self):
        self.responses = self.responses_class(self.config, self.instance)

    def __add_single_endpoint(self, endpoint_cls, path_name, is_protected):
        path_name = getattr(self.config, "path_to_{}".format(path_name))()
        if is_protected:
            endpoint_cls.decorators = [self.protected()]
        if self.instance_is_blueprint:
            path_name = self._get_url_prefix() + path_name
            if self.instance.url_prefix:
                path_name = path_name.replace(self.instance.url_prefix, "")
            self.instance.add_route(
                endpoint_cls.as_view(
                    config=self.config,
                    instance=self.instance,
                    responses=self.responses,
                ),
                path_name,
            )
        else:
            self.bp.add_route(
                endpoint_cls.as_view(
                    config=self.config,
                    instance=self.instance,
                    responses=self.responses,
                ),
                path_name,
            )

    def _get_url_prefix(self):
        bp_url_prefix = (
            self.bp.url_prefix if self.bp.url_prefix is not None else ""
        )
        config_url_prefix = self.config.url_prefix()
        url_prefix = bp_url_prefix + config_url_prefix
        return url_prefix

    @staticmethod
    def __get_app(instance, app=None):
        if isinstance(instance, Sanic):
            return instance

        elif isinstance(instance, Blueprint):
            if app is not None:
                return app

        raise exceptions.InitializationFailure

    def __initialize_bp(self):
        if isinstance(self.instance, Sanic):
            bp_name = self.config.blueprint_name()
            self.bp = Blueprint(bp_name)

        elif isinstance(self.instance, Blueprint):
            self.bp = self.instance

        else:
            raise exceptions.InitializationFailure  # noqa see line above

    def protected(self, *args, **kwargs):
        args = list(args)
        args.insert(0, self.instance)
        return protected(*args, **kwargs)

    def scoped(self, scopes, **kwargs):
        kwargs.update({"initialized_on": self.instance})
        return scoped(scopes, **kwargs)

    def inject_user(self, *args, **kwargs):
        args = list(args)
        args.insert(0, self.instance)
        return inject_user(*args, **kwargs)

    @property
    def instance_is_blueprint(self):
        return isinstance(self.instance, Blueprint)

    @staticmethod
    def __raise_if_not_none(exc):
        if exc is not None:
            raise exc
