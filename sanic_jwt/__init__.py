from sanic.response import text

from sanic_jwt.blueprint import bp as sanic_jwt_auth_bp
from sanic_jwt.authentication import SanicJWTAuthentication

from sanic_jwt import settings
from sanic_jwt import exceptions
from sanic_jwt import utils
from sanic.views import HTTPMethodView


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
            try:
                if issubclass(view, HTTPMethodView) and isinstance(route, str):
                    sanic_jwt_auth_bp.add_route(
                                      view.as_view(),
                                      route,
                                      strict_slashes=app.config.SANIC_JWT_STRICT_SLASHES
                                    )
                else:
                    raise exceptions.InvalidClassViewsFormat()
            except TypeError:
                raise exceptions.InvalidClassViewsFormat()

    # Add blueprint
    # sanic_jwt_auth_bp.strict_slashes = app.strict_slashes
    app.blueprint(sanic_jwt_auth_bp, url_prefix=app.config.SANIC_JWT_URL_PREFIX)

    # Setup authentication module
    app.auth = SanicJWTAuthentication(app, authenticate)
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
