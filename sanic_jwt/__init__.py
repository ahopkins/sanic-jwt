from sanic_jwt.blueprint import bp as sanic_jwt_auth_bp
from sanic_jwt.authentication import SanicJWTAuthentication
from sanic_jwt import settings, exceptions, utils


def initialize(
    app,
    authenticate,
    class_views=None,
    store_refresh_token=None,
    retrieve_refresh_token=None,
    retrieve_user=None,
):
    # Add settings
    utils.load_settings(app, settings)

    if class_views is not None:
        # TODO:
        # - Run some verifications that class_views is formatted
        #   ('<SOME ROUTE>', ClassInheritedFromHTTPMethodView)
        for route, view in class_views:
            sanic_jwt_auth_bp.add_route(view.as_view(), route)

    # Add blueprint
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
