import pytest
from sanic import Sanic
from sanic_jwt import initialize
from sanic_jwt import exceptions


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
