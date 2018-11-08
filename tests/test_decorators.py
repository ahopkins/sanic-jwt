from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.response import json
from sanic.response import text
from sanic_jwt import Initialize
from sanic_jwt.decorators import protected
from sanic_jwt.decorators import scoped
from sanic_jwt.decorators import inject_user


def test_forgotten_initialized_on_protected():
    blueprint = Blueprint("Test")

    @blueprint.get("/protected")
    @protected()
    def protected_hello_world(request):
        return json({"message": "hello world"})

    @blueprint.route("/scoped")
    @scoped("something")
    async def scoped_endpoint(request):
        return json({"scoped": True})

    app = Sanic()

    sanicjwt = Initialize(blueprint, app=app, authenticate=lambda x: True)

    app.blueprint(blueprint, url_prefix="/test")

    _, response = app.test_client.post(
        "/test/auth", json={"username": "user1", "password": "abcxyz"}
    )

    access_token = response.json.get(sanicjwt.config.access_token_name(), None)

    _, response = app.test_client.get(
        "/test/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 500
    assert response.json.get("exception") == "SanicJWTException"

    _, response = app.test_client.get(
        "/test/scoped",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 500
    assert response.json.get("exception") == "SanicJWTException"


def test_option_method_on_protected(app):
    sanic_app, sanic_jwt = app

    @sanic_app.route("/protected/options", methods=["OPTIONS"])
    @sanic_jwt.protected()
    async def my_protected_options(request):
        return text("", status=204)

    _, response = sanic_app.test_client.options("/protected/options")

    assert response.status == 204


def test_inject_user_regular(app_with_retrieve_user):
    sanic_app, sanic_jwt = app_with_retrieve_user
    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    @sanic_app.route("/protected/user")
    @inject_user()
    @protected()
    async def my_protected_user(request, user):
        return json({"user_id": user.user_id})

    access_token = response.json.get(
        sanic_jwt.config.access_token_name(), None
    )

    _, response = sanic_app.test_client.get(
        "/auth/me", headers={"Authorization": "Bearer {}".format(access_token)}
    )

    assert response.json.get("me").get("user_id") == 1

    _, response = sanic_app.test_client.get(
        "/protected/user",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )
    assert response.status == 200
    assert response.json.get("user_id") == 1


def test_inject_user_on_instance(app_with_retrieve_user):
    sanic_app, sanic_jwt = app_with_retrieve_user
    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    @sanic_app.route("/protected/user")
    @sanic_jwt.inject_user()
    @sanic_jwt.protected()
    async def my_protected_user(request, user):
        return json({"user_id": user.user_id})

    access_token = response.json.get(
        sanic_jwt.config.access_token_name(), None
    )

    _, response = sanic_app.test_client.get(
        "/auth/me", headers={"Authorization": "Bearer {}".format(access_token)}
    )

    assert response.json.get("me").get("user_id") == 1

    _, response = sanic_app.test_client.get(
        "/protected/user",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )
    assert response.status == 200
    assert response.json.get("user_id") == 1


def test_inject_user_on_instance_bp(app_with_retrieve_user):
    sanic_app, sanic_jwt = app_with_retrieve_user
    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    @sanic_app.route("/protected/user")
    @sanic_jwt.inject_user()
    @sanic_jwt.protected()
    async def my_protected_user(request, user):
        return json({"user_id": user.user_id})

    access_token = response.json.get(
        sanic_jwt.config.access_token_name(), None
    )

    _, response = sanic_app.test_client.get(
        "/auth/me", headers={"Authorization": "Bearer {}".format(access_token)}
    )

    assert response.json.get("me").get("user_id") == 1

    _, response = sanic_app.test_client.get(
        "/protected/user",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )
    assert response.status == 200
    assert response.json.get("user_id") == 1


def test_inject_user_on_instance_non_async(app_with_retrieve_user):
    sanic_app, sanic_jwt = app_with_retrieve_user
    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    @sanic_app.route("/protected/user")
    @sanic_jwt.inject_user()
    @sanic_jwt.protected()
    def my_protected_user(request, user):
        return json({"user_id": user.user_id})

    access_token = response.json.get(
        sanic_jwt.config.access_token_name(), None
    )

    _, response = sanic_app.test_client.get(
        "/auth/me", headers={"Authorization": "Bearer {}".format(access_token)}
    )

    assert response.json.get("me").get("user_id") == 1

    _, response = sanic_app.test_client.get(
        "/protected/user",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )
    assert response.status == 200
    assert response.json.get("user_id") == 1


def test_inject_user_with_auth_mode_off(app_with_retrieve_user):

    async def retrieve_user(request, payload, *args, **kwargs):
        return {"user_id": 123}

    microservice_app = Sanic()
    microservice_sanic_jwt = Initialize(
        microservice_app, auth_mode=False, retrieve_user=retrieve_user
    )

    @microservice_app.route("/protected/user")
    @microservice_sanic_jwt.inject_user()
    @microservice_sanic_jwt.protected()
    async def my_protected_user(request, user):
        return json({"user_id": user.get("user_id")})

    sanic_app, sanic_jwt = app_with_retrieve_user
    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    access_token = response.json.get(
        sanic_jwt.config.access_token_name(), None
    )

    _, response = microservice_app.test_client.get(
        "/protected/user",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 200
    assert response.json.get("user_id") == 123

    _, response = microservice_app.test_client.get("/protected/user")

    assert response.status == 401
