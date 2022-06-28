import pytest
from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.response import json

from sanic_jwt import Authentication, Initialize, protected, scoped


@pytest.fixture
def fixtures():
    blueprint = Blueprint("Test")
    cache = {}

    @blueprint.get("/", strict_slashes=True)
    @protected(blueprint)
    def protected_hello_world(request):
        return json({"message": "hello world"})

    @blueprint.get("/user/<id>", strict_slashes=True)
    @protected(blueprint)
    def protected_user(request, id):
        return json({"user": id})

    @blueprint.route("/scoped_empty")
    @scoped("something", initialized_on=blueprint)
    async def scoped_handler(request):
        return json({"scoped": True})

    class MyAuthentication(Authentication):
        async def authenticate(self, request, *args, **kwargs):
            return {"user_id": 1}

        async def store_refresh_token(
            self, user_id, refresh_token, *args, **kwargs
        ):
            key = "refresh_token_{user_id}".format(user_id=user_id)
            cache[key] = refresh_token

        async def retrieve_refresh_token(self, user_id, *args, **kwargs):
            key = "refresh_token_{user_id}".format(user_id=user_id)
            token = cache.get(key, None)
            return token

        async def retrieve_user(self, request, payload, *args, **kwargs):
            return {"user_id": 1}

    app = Sanic("sanic-jwt-test")

    sanicjwt = Initialize(
        blueprint,
        app=app,
        authentication_class=MyAuthentication,
        refresh_token_enabled=True,
    )

    app.blueprint(blueprint, url_prefix="/test")
    return blueprint, app, sanicjwt


def test_protected_blueprint(fixtures):
    blueprint, app, sanicjwt = fixtures
    _, response = app.test_client.get("/test/")

    assert response.status == 401
    assert response.json.get("exception") == "Unauthorized"
    assert "Authorization header not present." in response.json.get("reasons")

    _, response = app.test_client.post(
        "/test/auth", json={"username": "user1", "password": "abcxyz"}
    )

    assert response.status == 200

    access_token = response.json.get(sanicjwt.config.access_token_name(), None)

    assert access_token is not None

    _, response = app.test_client.get(
        "/test/", headers={"Authorization": "Bearer {}".format(access_token)}
    )

    assert response.status == 200
    assert response.json.get("message") == "hello world"


def test_scoped_empty(fixtures):
    blueprint, app, sanicjwt = fixtures
    _, response = app.test_client.get("/test/scoped_empty")
    assert response.status == 401
    assert response.json.get("exception") == "Unauthorized"
    assert "Authorization header not present." in response.json.get("reasons")


def test_authentication_all_methods(fixtures):
    blueprint, app, sanicjwt = fixtures

    _, response = app.test_client.post(
        "/test/auth", json={"username": "user1", "password": "abcxyz"}
    )

    assert response.status == 200
    assert sanicjwt.config.access_token_name() in response.json
    assert sanicjwt.config.refresh_token_name() in response.json

    access_token = response.json.get(sanicjwt.config.access_token_name(), None)
    refresh_token = response.json.get(
        sanicjwt.config.refresh_token_name(), None
    )

    assert access_token is not None
    assert refresh_token is not None

    _, response = app.test_client.get(
        "/test/",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 200
    assert response.json.get("message") == "hello world"

    _, response = app.test_client.get(
        "/test/auth/verify",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 200

    _, response = app.test_client.get(
        "/test/auth/me",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 200
    assert "me" in response.json

    _, response = app.test_client.post(
        "/test/auth/refresh",
        headers={"Authorization": "Bearer {}".format(access_token)},
        json={sanicjwt.config.refresh_token_name(): refresh_token},
    )

    new_access_token = response.json.get(
        sanicjwt.config.access_token_name(), None
    )

    assert response.status == 200
    assert new_access_token is not None
    assert (
        response.json.get(sanicjwt.config.refresh_token_name(), None) is None
    )  # there is no new refresh token
    assert sanicjwt.config.refresh_token_name() not in response.json
