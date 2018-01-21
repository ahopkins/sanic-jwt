from sanic import Sanic

import pytest
from sanic_jwt import exceptions, initialize


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
