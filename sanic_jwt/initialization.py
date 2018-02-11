from sanic import Blueprint
from sanic import Sanic
from sanic.response import text

from sanic_jwt.authentication import Authentication
from sanic_jwt.blueprint import bp as sanic_jwt_auth_bp
from sanic_jwt.configuration import Configuration
from sanic_jwt.configuration import get_config
from sanic_jwt.configuration import make_config
from sanic_jwt.configuration import defaults

from sanic.views import HTTPMethodView
from sanic_jwt import exceptions
# from sanic_jwt import settings
# from sanic_jwt import utils


# def initialize(
#     app,
#     authenticate,
#     class_views=None,
#     store_refresh_token=None,
#     retrieve_refresh_token=None,
#     retrieve_user=None
# ):
#     # Add settings
#     utils.load_settings(app, settings)

#     if class_views is not None:
#         for route, view in class_views:
#             if issubclass(view, HTTPMethodView) and isinstance(route, str):
#                 sanic_jwt_auth_bp.add_route(
#                     view.as_view(),
#                     route,
#                     strict_slashes=app.config.SANIC_JWT_STRICT_SLASHES
#                 )
#             else:
#                 raise exceptions.InvalidClassViewsFormat()

#     # Add blueprint
#     app.blueprint(sanic_jwt_auth_bp, url_prefix=app.config.SANIC_JWT_URL_PREFIX)

#     # Setup authentication module
#     app.auth = Authentication(app, authenticate)
#     if store_refresh_token:
#         setattr(app.auth, 'store_refresh_token', store_refresh_token)
#     if retrieve_refresh_token:
#         setattr(app.auth, 'retrieve_refresh_token', retrieve_refresh_token)
#     if retrieve_user:
#         setattr(app.auth, 'retrieve_user', retrieve_user)

#     if app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED and (
#         not store_refresh_token or
#         not retrieve_refresh_token
#     ):
#         raise exceptions.RefreshTokenNotImplemented()

#     @app.exception(exceptions.SanicJWTException)
#     def exception_response(request, exception):
#         return text(str(exception), status=exception.status_code)

def initialize(*args, **kwargs):
    if len(args) > 1:
        kwargs.update({'authenticate': args[1]})
    Initialize(args[0], **kwargs)


handlers = (
    ('authenticate', (),),
    ('store_refresh_token', ('refresh_token_enabled', ),),
    ('retrieve_refresh_token', ('refresh_token_enabled', ),),
    ('retrieve_user', (),),
    ('add_scopes_to_payload', ('scopes_enabled', ),),
)


class Initialize(object):
    configuration_class = Configuration
    authentication_class = Authentication

    def __init__(self, instance, app=None, **kwargs):
        app = self.__get_app(instance, app=app)
        self.app = app
        self.kwargs = kwargs

        self.instance = instance
        self.__load_configuration()
        self.__check_initialization()
        self.__add_class_views()
        self.__add_blueprint()
        self.__initialize_instance()

    def __add_blueprint(self):
        """
        Initialize the Sanic JWT Blueprint and add to the instance initialized
        """
        config = get_config()
        self.instance.blueprint(
            sanic_jwt_auth_bp, url_prefix=config.url_prefix)

    def __add_class_views(self):
        """
        Include any custom class views on the Sanic JWT Blueprint
        """
        config = get_config()
        if 'class_views' in self.kwargs:
            class_views = self.kwargs.pop('class_views')

            for route, view in class_views:
                if issubclass(view, HTTPMethodView) and isinstance(route, str):
                    sanic_jwt_auth_bp.add_route(
                        view.as_view(),
                        route,
                        strict_slashes=config.strict_slashes
                    )
                else:
                    raise exceptions.InvalidClassViewsFormat()

    def __check_initialization(self):
        """
        Confirm that required parameters were initialized and report back exceptions
        """
        config = get_config()
        if config.refresh_token_enabled and (
            'store_refresh_token' not in self.kwargs or
            'retrieve_refresh_token' not in self.kwargs
        ):
            raise exceptions.RefreshTokenNotImplemented

        # TODO:
        # - Add additional checks

    def __initialize_instance(self):
        """
        Take any predefined methods/handlers and insert them into Sanic JWT
        """
        # Initialize instance of the Authentication class
        self.instance.auth = self.authentication_class(self.app)

        if 'authenticate' not in self.kwargs:
            raise exceptions.AuthenticateNotImplemented

        for handler in handlers:
            handler_name, config_enable = handler
            if handler_name in self.kwargs:
                method = self.kwargs.pop(handler_name)
                setattr(self.instance.auth, handler_name, method)

        # TODO:
        # - Make this response into a handler
        @self.app.exception(exceptions.SanicJWTException)
        def exception_response(request, exception):
            return text(str(exception), status=exception.status_code)

    def __load_configuration(self):
        """
        Configure settings for the instance in the following order:

        1. Sanic JWT's defaults
        2. Custom Configuration class
        3. Key word arguments passed to Initialize
        """
        config_to_enable = [x for x in handlers if x[1]]
        for config_item in config_to_enable:
            if config_item[0] in self.kwargs:
                list(map(lambda x: self.kwargs.update(
                    {config_item[0]: True}), config_item[1]))

        config = self.configuration_class(self.app.config, **self.kwargs)
        make_config(config)
        for setting in dir(config):
            if setting in defaults:
                value = getattr(config, setting)
                key = '_'.join(['sanic', 'jwt', setting]).upper()
                # TODO:
                # - Need to localize this config to self.instance
                setattr(self.app.config, key, value)

    @staticmethod
    def __get_app(instance, app=None):
        if isinstance(instance, Sanic):
            return instance
        elif isinstance(instance, Blueprint):
            if app is not None:
                return app
        raise exceptions.InitializationFailure
