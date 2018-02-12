from sanic import Blueprint
from sanic import Sanic
from sanic.response import text
from sanic.views import HTTPMethodView
from sanic_jwt import exceptions
from sanic_jwt import endpoints
from sanic_jwt.authentication import Authentication
from sanic_jwt.configuration import Configuration
from sanic_jwt.response import Response
from sanic_jwt.response import make_response


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


class Initialize:
    """Class used to initialize Sanic JWT

    Must be initialized with a keyword argument: `authenticate` that is a
    method that MUST return a user object that when iterated upon returns a
    dictionary, or has a `to_dict` method. The resulting dictionary MUST
    have a key/value for a unique user id.
    """
    configuration_class = Configuration
    authentication_class = Authentication
    response_class = Response

    def __init__(self, instance, app=None, **kwargs):
        app = self.__get_app(instance, app=app)
        bp = self.__get_bp(instance)

        self.app = app
        self.bp = bp
        self.kwargs = kwargs
        self.instance = instance

        self.__load_configuration()
        self.__load_response()
        self.__check_initialization()
        self.__add_class_views()
        self.__add_endpoints()
        self.__initialize_instance()

    def __add_endpoints(self):
        """
        Initialize the Sanic JWT Blueprint and add to the instance initialized
        """
        config = self.config

        self.bp.add_route(endpoints.AuthenticateEndpoint.as_view(config=config), '/')
        self.bp.add_route(endpoints.RetrieveUserEndpoint.as_view(config=config), '/me')
        self.bp.add_route(endpoints.VerifyEndpoint.as_view(config=config), '/verify')
        self.bp.add_route(endpoints.RefreshEndpoint.as_view(config=config), '/refresh')

        if not self.instance_is_blueprint:
            self.instance.blueprint(
                self.bp, url_prefix=config.url_prefix)

    def __add_class_views(self):
        """
        Include any custom class views on the Sanic JWT Blueprint
        """
        config = self.config
        if 'class_views' in self.kwargs:
            class_views = self.kwargs.pop('class_views')

            for route, view in class_views:
                if issubclass(view, HTTPMethodView) and isinstance(route, str):
                    self.bp.add_route(
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
        config = self.config
        if hasattr(config, 'refresh_token_enabled') and \
            getattr(config, 'refresh_token_enabled') and (
            not self.kwargs.get('store_refresh_token') or
            not self.kwargs.get('retrieve_refresh_token')
        ):
            raise exceptions.RefreshTokenNotImplemented

        # TODO:
        # - Add additional checks

    def __initialize_instance(self):
        """
        Take any predefined methods/handlers and insert them into Sanic JWT
        """
        # Initialize instance of the Authentication class
        config = self.config
        self.instance.auth = self.authentication_class(self.app, config=config)

        if 'authenticate' not in self.kwargs:
            raise exceptions.AuthenticateNotImplemented

        for handler in handlers:
            handler_name, _ = handler
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
                    {x: True, config_item[0]: self.kwargs.get(config_item[0])}),
                    config_item[1]))

        self.config = self.configuration_class(self.app.config, **self.kwargs)

    def __load_response(self):
        response = self.response_class()
        make_response(response)

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
            return Blueprint('auth_bp')
        elif isinstance(instance, Blueprint):
            return instance
        raise exceptions.InitializationFailure

    @property
    def instance_is_blueprint(self):
        return isinstance(self.instance, Blueprint)
