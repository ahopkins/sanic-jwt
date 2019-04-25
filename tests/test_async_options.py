"""
Test code taken from:
https://github.com/ahopkins/sanic-jwt/issues/110#issue-330031252
"""


import jwt
from sanic import Blueprint, Sanic
from sanic.response import text
from sanic.views import HTTPMethodView

import pytest
from sanic_jwt import Authentication, initialize, protected

ALL_METHODS = ["GET", "OPTIONS"]


class TestMethodView(HTTPMethodView):
    async def options(self, *args, **kwargs):
        return text("ok")


class Tester(TestMethodView):
    decorators = [protected()]

    async def get(self, request):
        return text("ok")


bp = Blueprint("bp")
bp.add_route(Tester.as_view(), "/test", methods=ALL_METHODS)


class CustomAuth(Authentication):
    async def authenticate(self, request, *args, **kwargs):
        return {"username": "Rich", "password": "not secure"}

    async def retrieve_user(self, request, payload, *args, **kwargs):
        if payload:
            user_id = payload.get("username", None)
            passwd = payload.get("password", None)
            return {"username": user_id, "password": passwd}

    async def extend_payload(self, payload, user=None, *args, **kwargs):
        if user:
            payload.update({"extra_info": "awesome!"})
        return payload


@pytest.fixture
def app():
    app = Sanic(__name__)
    app.config.SANIC_JWT_AUTHORIZATION_HEADER_PREFIX = "JWT"
    app.config.SANIC_JWT_EXPIRATION_DELTA = 360000
    app.config.SANIC_JWT_USER_ID = "username"

    sanicjwt = initialize(app, authentication_class=CustomAuth)
    app.blueprint(bp)

    return app, sanicjwt


def test_async_options(app):
    sanic_app, sanicjwt = app
    _, response = sanic_app.test_client.get("/test")
    assert response.status == 401
    assert "Authorization header not present." in response.json.get("reasons")

    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "Rich", "password": "not secure"}
    )

    access_token = response.json.get(sanicjwt.config.access_token_name(), None)

    payload = jwt.decode(
        access_token,
        sanicjwt.config.secret(),
        algorithms=sanicjwt.config.algorithm(),
    )

    assert "extra_info" in payload
    assert payload.get("extra_info") == "awesome!"

    assert response.status == 200
    assert access_token is not None

    _, response = sanic_app.test_client.get(
        "/test/", headers={"Authorization": "JWT {}".format(access_token)}
    )

    assert response.status == 200
    assert response.body == b"ok"

    _, response = sanic_app.test_client.options("/test")
    # print(response.body)

    assert response.status == 200
    assert response.body == b"ok"
