import pytest
from datetime import datetime, timedelta

import jwt
from freezegun import freeze_time
from sanic.response import json
from sanic_jwt.decorators import protected


@pytest.fixture
def access_token(app):
    sanic_app, sanic_jwt = app
    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )
    return response.json.get(sanic_jwt.config.access_token_name(), None)


def test_me(app, access_token):
    sanic_app, _ = app
    _, response = sanic_app.test_client.get(
        "/auth/me", headers={"Authorization": "Bearer {}".format(access_token)}
    )

    assert response.status == 500
    assert response.json.get("exception") == "MeEndpointNotSetup"


def test_expired(app_with_retrieve_user):
    sanic_app, sanic_jwt = app_with_retrieve_user
    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    @sanic_app.route("/protected/user")
    @protected()
    async def my_protected_user(request, user):
        return json({"user_id": user.user_id})

    access_token = response.json.get(
        sanic_jwt.config.access_token_name(), None
    )
    payload = jwt.decode(access_token, sanic_jwt.config.secret())
    exp = payload.get("exp", None)

    assert "exp" in payload

    exp = datetime.utcfromtimestamp(exp)

    with freeze_time(datetime.utcnow() + timedelta(seconds=(60 * 35))):
        assert isinstance(exp, datetime)
        assert datetime.utcnow() > exp

        _, response = sanic_app.test_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403
        assert response.json.get("exception") == "Unauthorized"
        assert "Signature has expired." in response.json.get("reasons")

        _, response = sanic_app.test_client.get(
            "/protected/user",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403
        assert response.json.get("exception") == "Unauthorized"
        assert "Signature has expired." in response.json.get("reasons")
