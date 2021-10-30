from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.response import json

from sanic_jwt import Initialize
from sanic_jwt.decorators import protected


@pytest.fixture
def bp():
    blueprint = Blueprint("Test1", url_prefix="/test1")

    @blueprint.get("/", strict_slashes=True)
    @protected(blueprint)
    def protected_hello_world_bp(request):
        return json({"type": "bp"})

    return blueprint


@pytest.fixture
def app(bp):
    app = Sanic("sanic-jwt-test")

    @app.get("/", strict_slashes=True)
    @protected()
    def protected_hello_world_app(request):
        return json({"type": "app"})

    return app


async def authenticate1(request, *args, **kwargs):
    return {"user_id": 1}


async def authenticate2(request, *args, **kwargs):
    return {"user_id": 2}


@pytest.fixture
def sanicjwt1(bp, app):
    return Initialize(bp, app=app, authenticate=authenticate1)


@pytest.fixture
def sanicjwt2(app):
    return Initialize(
        app,
        authenticate=authenticate2,
        url_prefix="/a",
        access_token_name="token",
        cookie_access_token_name="token",
        cookie_set=True,
        secret="somethingdifferent",
    )


def test_protected_blueprints(app, bp, sanicjwt1, sanicjwt2):
    app.blueprint(bp)

    _, response1 = app.test_client.post(
        "/test1/auth", json={"username": "user1", "password": "abcxyz"}
    )
    _, response2 = app.test_client.post(
        "/a", json={"username": "user1", "password": "abcxyz"}
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
        "/",
        cookies={sanicjwt2.config.cookie_access_token_name(): access_token_2},
    )

    assert response1.status == 200
    assert response2.status == 200
    assert response1.json.get("type") == "bp"
    assert response2.json.get("type") == "app"

    _, response1 = app.test_client.get(
        "/test1/",
        headers={"Authorization": "Bearer {}".format(access_token_2)},
    )
    _, response2 = app.test_client.get(
        "/",
        cookies={sanicjwt2.config.cookie_access_token_name(): access_token_1},
    )

    assert response1.status == 401
    assert response1.json.get("exception") == "Unauthorized"
    assert "Auth required." in response1.json.get("reasons")
    assert response2.status == 401
    assert response2.json.get("exception") == "Unauthorized"
    assert "Auth required." in response2.json.get("reasons")


def test_protected_blueprints_debug(app, bp, sanicjwt1, sanicjwt2):
    app.blueprint(bp, url_prefix="/test1")

    sanicjwt1.config.debug.update(True)
    sanicjwt2.config.debug.update(True)

    _, response1 = app.test_client.post(
        "/test1/auth", json={"username": "user1", "password": "abcxyz"}
    )
    _, response2 = app.test_client.post(
        "/a", json={"username": "user1", "password": "abcxyz"}
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
        "/",
        cookies={sanicjwt2.config.cookie_access_token_name(): access_token_1},
    )

    assert response1.status == 400
    assert response1.json.get("exception") == "Unauthorized"
    assert "Signature verification failed." in response1.json.get("reasons")
    assert response2.status == 400
    assert response2.json.get("exception") == "Unauthorized"
    assert "Signature verification failed." in response2.json.get("reasons")
