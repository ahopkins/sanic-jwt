import pytest
from sanic import Sanic

import jwt
from sanic_jwt import exceptions, Initialize


def test_secret_not_enabled():
    app = Sanic(__name__)
    with pytest.raises(exceptions.UserSecretNotImplemented):
        sanicjwt = Initialize(
            app,
            authenticate=lambda: {},
            user_secret_enabled=True,
        )


@pytest.mark.asyncio
async def test_user_secret(app_with_user_secrets):
    app, sanicjwt = app_with_user_secrets

    _, response = await app.asgi_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    access_token = response.json().get(
        sanicjwt.config.access_token_name(), None
    )

    secret = await app.auth._get_secret(token=access_token)

    assert access_token
    assert secret == "foobar<1>"

    _, response = await app.asgi_client.get(
        "/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 200
    assert response.json().get("protected") is True
