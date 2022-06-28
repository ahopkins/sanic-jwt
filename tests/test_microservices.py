# import pytest

from sanic import Sanic
from sanic.response import json

from sanic_jwt import Initialize


async def authenticate(username_table):
    return {"user_id": 1}


def test_microservice_simple():
    microservice_app = Sanic("sanic-jwt-test")
    Initialize(microservice_app, auth_mode=False)

    microservice_app.route("/")(lambda _: ...)

    _, response = microservice_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    assert response.status == 404


def test_microservice_interaction():
    microservice_app = Sanic("sanic-jwt-test-microservice")
    microservice_sanic_jwt = Initialize(microservice_app, auth_mode=False)

    @microservice_app.route("/protected")
    @microservice_sanic_jwt.protected()
    async def protected_request(request):
        return json({"protected": True})

    app = Sanic("sanic-jwt-test-app")
    sanic_jwt = Initialize(app, authenticate=authenticate)

    _, response = microservice_app.test_client.get("/protected")

    assert response.status == 401
    assert response.json.get("exception") == "Unauthorized"
    assert "Authorization header not present." in response.json.get("reasons")

    _, response = app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    access_token = response.json.get(
        sanic_jwt.config.access_token_name(), None
    )
    assert response.status == 200
    assert access_token is not None

    _, response = microservice_app.test_client.get(
        "/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 200
    assert response.json.get("protected") is True
