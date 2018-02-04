from sanic import Blueprint
from sanic import Sanic
from sanic.response import text

from sanic_jwt.authentication import Authentication
from sanic_jwt.blueprint import bp as sanic_jwt_auth_bp
from sanic_jwt.configuration import Configuration

from sanic.views import HTTPMethodView
from sanic_jwt import exceptions
from sanic_jwt import settings
from sanic_jwt import utils


def initialize(
    app,
    authenticate,
    class_views=None,
    store_refresh_token=None,
    retrieve_refresh_token=None,
    retrieve_user=None
):
    # Add settings
    utils.load_settings(app, settings)

    if class_views is not None:
        for route, view in class_views:
            if issubclass(view, HTTPMethodView) and isinstance(route, str):
                sanic_jwt_auth_bp.add_route(
                    view.as_view(),
                    route,
                    strict_slashes=app.config.SANIC_JWT_STRICT_SLASHES
                )
            else:
                raise exceptions.InvalidClassViewsFormat()

    # Add blueprint
    app.blueprint(sanic_jwt_auth_bp, url_prefix=app.config.SANIC_JWT_URL_PREFIX)

    # Setup authentication module
    app.auth = Authentication(app, authenticate)
    if store_refresh_token:
        setattr(app.auth, 'store_refresh_token', store_refresh_token)
    if retrieve_refresh_token:
        setattr(app.auth, 'retrieve_refresh_token', retrieve_refresh_token)
    if retrieve_user:
        setattr(app.auth, 'retrieve_user', retrieve_user)

    if app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED and (
        not store_refresh_token or
        not retrieve_refresh_token
    ):
        raise exceptions.RefreshTokenNotImplemented()

    @app.exception(exceptions.SanicJWTException)
    def exception_response(request, exception):
        return text(str(exception), status=exception.status_code)


class Initialize(object):
    configuration_class = Configuration
    authentication_class = Authentication

    def __init__(self, instance, app=None, **kwargs):
        app = self.__get_app(instance, app=app)

        try:
            authenticate = kwargs.pop('authenticate')
            instance.auth = self.authentication_class(app, authenticate)
        except KeyError:
            raise exceptions.AuthenticateNotImplemented

        self.app = app
        self.instance = instance
        self.__load_configuration(kwargs)

    def __load_configuration(self, kwargs):
        self.config = self.configuration_class(self.app.config, **kwargs)
        for setting in dir(self.config):
            if not setting.startswith('__'):
                value = getattr(self.config, setting)
                key = '_'.join(['sanic', 'jwt', setting]).upper()
                setattr(self.app.config, key, value)

    @staticmethod
    def __get_app(instance, app=None):
        if isinstance(instance, Sanic):
            return instance
        elif isinstance(instance, Blueprint):
            if app is not None:
                return app
        raise exceptions.InitializationFailure
