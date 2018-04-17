import inspect
from collections import namedtuple

from sanic import Blueprint, Sanic

from sanic_jwt import endpoints, exceptions
from sanic_jwt.authentication import Authentication
from sanic_jwt.configuration import Configuration
from sanic_jwt.decorators import protected, scoped
from sanic_jwt.responses import Responses

_Handler = namedtuple("_Handler", ["name", "keys", "exception"])


def initialize(*args, **kwargs):
    if len(args) > 1:
        kwargs.update({"authenticate": args[1]})
    return Initialize(args[0], **kwargs)


handlers = (
    _Handler("authenticate", None, exceptions.AuthenticateNotImplemented),
    _Handler(
        "store_refresh_token",
        ["refresh_token_enabled"],
        exceptions.RefreshTokenNotImplemented,
    ),
    _Handler(
        "retrieve_refresh_token",
        ["refresh_token_enabled"],
        exceptions.RefreshTokenNotImplemented,
    ),
    _Handler("retrieve_user", None, None),
    _Handler(
        "add_scopes_to_payload",
        ["scopes_enabled"],
        exceptions.ScopesNotImplemented,
    ),
    _Handler("extend_payload", None, None),
)

init_classes = (
    "configuration_class", "authentication_class", "responses_class"
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
        bp = self.__get_bp(instance)

        self.app = app
        self.bp = bp
        self.kwargs = kwargs
        self.instance = instance

        self.__check_deprecated()
        self.__check_classes()
        self.__load_configuration()
        self.__load_responses()

        if self.config.auth_mode():
            self.__add_class_views()
            self.__add_endpoints()

        self.__initialize_instance()

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
        endpoint_mappings = (
            ("AuthenticateEndpoint", "authenticate"),
            ("RetrieveUserEndpoint", "retrieve_user"),
            ("VerifyEndpoint", "verify"),
            ("RefreshEndpoint", "refresh"),
        )

        for endpoint in endpoint_mappings:
            self.__add_single_endpoint(*endpoint)

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
                if (
                    issubclass(view, endpoints.BaseEndpoint)
                    and isinstance(route, str)
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
        msg = "Sanic JWT was not initialized properly. It did not " "received an instance of {}"
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

        if config.auth_mode():
            # check if kwargs methods contains authentication methods or if
            # the authentication auth already has them (if subclassed)

            for handler in handlers:
                if handler.keys is None:
                    self.__check_method_in_auth(
                        handler.name, handler.exception
                    )
                else:
                    if all(map(lambda k: config.get(k), handler.keys)):
                        self.__check_method_in_auth(
                            handler.name, handler.exception
                        )

            for handler in handlers:
                if handler.name in self.kwargs:
                    method = self.kwargs.pop(handler.name)
                    setattr(self.instance.auth, handler.name, method)

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

    def __add_single_endpoint(self, class_name, path_name):
        view = getattr(endpoints, class_name)
        path_name = getattr(self.config, "path_to_{}".format(path_name))()
        if self.instance_is_blueprint:
            path_name = self._get_url_prefix() + path_name
            self.instance.add_route(
                view.as_view(
                    config=self.config,
                    instance=self.instance,
                    responses=self.responses,
                ),
                path_name,
            )
        else:
            self.bp.add_route(
                view.as_view(
                    config=self.config,
                    instance=self.instance,
                    responses=self.responses,
                ),
                path_name,
            )

    def _get_url_prefix(self):
        bp_url_prefix = self.bp.url_prefix if self.bp.url_prefix is not None else ""
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

    @staticmethod
    def __get_bp(instance):
        if isinstance(instance, Sanic):
            return Blueprint("auth_bp")

        elif isinstance(instance, Blueprint):
            return instance

        raise exceptions.InitializationFailure

    def protected(self, *args, **kwargs):
        args = list(args)
        args.insert(0, self.instance)
        return protected(*args, **kwargs)

    def scoped(self, scopes, **kwargs):
        kwargs.update({"initialized_on": self.instance})
        return scoped(scopes, **kwargs)

    @property
    def instance_is_blueprint(self):
        return isinstance(self.instance, Blueprint)

    @staticmethod
    def __raise_if_not_none(exc):
        if exc is not None:
            raise exc
