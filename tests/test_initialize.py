from sanic import Blueprint
from sanic import Sanic

import pytest

from sanic_jwt import Initialize
from sanic_jwt import exceptions
from sanic_jwt import initialize


def test_store_refresh_token_and_retrieve_refresh_token_ommitted():
    app = Sanic()
    app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED = True

    with pytest.raises(exceptions.RefreshTokenNotImplemented):
        initialize(
            app,
            authenticate=lambda: True,
        )


def test_store_refresh_token_ommitted():
    app = Sanic()
    app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED = True

    with pytest.raises(exceptions.RefreshTokenNotImplemented):
        initialize(
            app,
            authenticate=lambda: True,
            retrieve_refresh_token=lambda: True,
        )


def test_retrieve_refresh_token_ommitted():
    app = Sanic()
    app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED = True

    with pytest.raises(exceptions.RefreshTokenNotImplemented):
        initialize(
            app,
            authenticate=lambda: True,
            store_refresh_token=lambda: True,
        )


def test_store_refresh_token_and_retrieve_refresh_token_drfined():
    app = Sanic()
    app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED = True

    initialize(
        app,
        authenticate=lambda: True,
        store_refresh_token=lambda: True,
        retrieve_refresh_token=lambda: True,
    )

    assert True


def test_invalid_classview():
    app = Sanic()

    class NotAView(object):
        pass

    with pytest.raises(exceptions.InvalidClassViewsFormat):
        initialize(
            app, authenticate=lambda: True, class_views=[(object, NotAView)])


def test_initialize_class_missing_authenticate():
    app = Sanic()

    with pytest.raises(exceptions.AuthenticateNotImplemented):
        Initialize(app)


def test_initialize_class():
    app = Sanic()
    Initialize(app, authenticate=lambda: True)

    assert True


def test_initialize_class_on_blueprint_missing_app():
    app = Sanic()
    bp = Blueprint('test')
    app.blueprint(bp)

    with pytest.raises(exceptions.InitializationFailure):
        Initialize(bp, authenticate=lambda: True)


def test_initialize_class_on_blueprint():
    app = Sanic()
    bp = Blueprint('test')
    app.blueprint(bp)

    Initialize(bp, app=app, authenticate=lambda: True)

    assert True
