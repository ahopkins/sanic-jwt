from sanic_jwt.blueprint import bp as sanic_jwt_auth_bp
from sanic_jwt.authentication import SanicJWTAuthentication
from sanic_jwt import settings
from sanic.views import HTTPMethodView


def initialize(
    app,
    authenticate,
    class_views=None,
    store_refresh_token=None,
    retrieve_refresh_token=None,
    retrieve_user=None,
):
    # Add settings
    app.config.from_object(settings)

    if class_views is not None:
        for route, view in class_views:
            try:
                if issubclass(view, HTTPMethodView) and isinstance(route, str):
                    sanic_jwt_auth_bp.add_route(view.as_view(), route)
                else:
                    raise Exception("class_views should follow this format ('<SOME ROUTE>', ClassInheritedFromHTTPMethodView)")
            except TypeError:
                raise Exception("class_views should follow this format ('<SOME ROUTE>', ClassInheritedFromHTTPMethodView)")

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
