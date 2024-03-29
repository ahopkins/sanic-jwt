import pytest
from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.response import json

from sanic_jwt import Initialize
from sanic_jwt.decorators import protected


@pytest.fixture
def fixtures():
    blueprint1 = Blueprint("Test1")
    blueprint2 = Blueprint("Test2")

    @blueprint1.get("/", strict_slashes=True)
    @protected(blueprint1)
    def protected_hello_world_1(request):
        return json({"version": 1})

    @blueprint2.get("/", strict_slashes=True)
    @protected(blueprint2)
    def protected_hello_world_2(request):
        return json({"version": 2})

    async def authenticate(request, *args, **kwargs):
        return {"user_id": 1}

    app = Sanic("sanic-jwt-test")

    sanicjwt1 = Initialize(blueprint1, app=app, authenticate=authenticate)

    sanicjwt2 = Initialize(
        blueprint2,
        app=app,
        authenticate=authenticate,
        url_prefix="/a",
        access_token_name="token",
        cookie_access_token_name="token",
        cookie_set=True,
        secret="somethingdifferent",
    )

    app.blueprint(blueprint1, url_prefix="/test1")
    app.blueprint(blueprint2, url_prefix="/test2")

    return blueprint1, blueprint2, app, sanicjwt1, sanicjwt2


def test_protected_blueprints(fixtures):
    blueprint1, blueprint2, app, sanicjwt1, sanicjwt2 = fixtures
    _, response1 = app.test_client.get("/test1/")
    _, response2 = app.test_client.get("/test2/")

    assert response1.status == 401
    assert response1.json.get("exception") == "Unauthorized"
    assert "Authorization header not present." in response1.json.get("reasons")
    assert response2.status == 401
    assert response2.json.get("exception") == "Unauthorized"
    assert "Authorization cookie not present." in response2.json.get("reasons")

    _, response1 = app.test_client.post(
        "/test1/auth", json={"username": "user1", "password": "abcxyz"}
    )
    _, response2 = app.test_client.post(
        "/test2/a", json={"username": "user1", "password": "abcxyz"}
    )

    assert response1.status == 200
    assert response2.status == 200

    access_token_1 = response1.json.get(
        sanicjwt1.config.access_token_name(), None
    )
    access_token_2 = response2.json.get(
        sanicjwt2.config.access_token_name(), None
    )

    assert access_token_1 is not None
    assert access_token_2 is not None

    wrong_token_grab_1 = response1.json.get(
        sanicjwt2.config.access_token_name(), None
    )
    wrong_token_grab_2 = response2.json.get(
        sanicjwt1.config.access_token_name(), None
    )

    assert wrong_token_grab_1 is None
    assert wrong_token_grab_2 is None

    _, response1 = app.test_client.get(
        "/test1/",
        headers={"Authorization": "Bearer {}".format(access_token_1)},
    )
    _, response2 = app.test_client.get(
        "/test2/",
        cookies={sanicjwt2.config.cookie_access_token_name(): access_token_2},
    )

    assert response1.status == 200
    assert response2.status == 200
    assert response1.json.get("version") == 1
    assert response2.json.get("version") == 2

    _, response1 = app.test_client.get(
        "/test1/",
        headers={"Authorization": "Bearer {}".format(access_token_2)},
    )
    _, response2 = app.test_client.get(
        "/test2/",
        cookies={sanicjwt2.config.cookie_access_token_name(): access_token_1},
    )

    assert response1.status == 401
    assert response1.json.get("exception") == "Unauthorized"
    assert "Auth required." in response1.json.get("reasons")
    assert response2.status == 401
    assert response2.json.get("exception") == "Unauthorized"
    assert "Auth required." in response2.json.get("reasons")


def test_protected_blueprints_debug(fixtures):
    blueprint1, blueprint2, app, sanicjwt1, sanicjwt2 = fixtures
    sanicjwt1.config.debug.update(True)
    sanicjwt2.config.debug.update(True)

    _, response1 = app.test_client.post(
        "/test1/auth", json={"username": "user1", "password": "abcxyz"}
    )
    _, response2 = app.test_client.post(
        "/test2/a", json={"username": "user1", "password": "abcxyz"}
    )

    access_token_1 = response1.json.get(
        sanicjwt1.config.access_token_name(), None
    )
    access_token_2 = response2.json.get(
        sanicjwt2.config.access_token_name(), None
    )

    _, response1 = app.test_client.get(
        "/test1/",
        headers={"Authorization": "Bearer {}".format(access_token_2)},
    )
    _, response2 = app.test_client.get(
        "/test2/",
        cookies={sanicjwt2.config.cookie_access_token_name(): access_token_1},
    )

    assert response1.status == 400
    assert response1.json.get("exception") == "Unauthorized"
    assert "Signature verification failed." in response1.json.get("reasons")
    assert response2.status == 400
    assert response2.json.get("exception") == "Unauthorized"
    assert "Signature verification failed." in response2.json.get("reasons")
