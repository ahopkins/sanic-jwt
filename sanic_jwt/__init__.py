from sanic_jwt.blueprint import bp as sanic_jwt_auth_bp
from sanic_jwt.authentication import SanicJWTAuthentication
from sanic_jwt import settings


def initialize(app, authenticate):
    app.blueprint(sanic_jwt_auth_bp, url_prefix='/auth')
    app.auth = SanicJWTAuthentication(app, authenticate)
    app.config.from_object(settings)
