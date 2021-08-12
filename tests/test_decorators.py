from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.response import html, json, text

from sanic_jwt import Initialize
from sanic_jwt.decorators import inject_user, protected, scoped


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

    app = Sanic("sanic-jwt-test")

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

    sanic_app.router.reset()

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

    sanic_app.router.reset()

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

    sanic_app.router.reset()

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

    sanic_app.router.reset()

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

    microservice_app = Sanic("sanic-jwt-test")
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


def test_redirect_without_url(app):
    sanic_app, sanic_jwt = app

    @sanic_app.route("/index.html")
    def index(request):
        return html("<html><body>Home</body></html>")

    @sanic_app.route("/protected/static")
    @sanic_jwt.protected(redirect_on_fail=True)
    async def my_protected_static(request):
        return text("", status=200)

    request, response = sanic_app.test_client.get("/protected/static")

    assert response.status == 200
    assert response.body == b"<html><body>Home</body></html>"
    assert response.history
    assert response.history[0].status_code == 302


def test_redirect_with_decorator_url(app):
    sanic_app, sanic_jwt = app

    @sanic_app.route("/protected/static")
    @sanic_jwt.protected(redirect_on_fail=True, redirect_url="/unprotected")
    async def my_protected_static(request):
        return text("", status=200)

    @sanic_app.route("/unprotected")
    async def my_unprotected_goto(request):
        return text("unprotected content", status=200)

    _, response = sanic_app.test_client.get("/protected/static")

    assert response.status == 200 and response.text == "unprotected content"


def test_redirect_with_configured_url():
    sanic_app = Sanic("sanic-jwt-test")
    sanic_jwt = Initialize(
        sanic_app, auth_mode=False, login_redirect_url="/unprotected"
    )

    @sanic_app.route("/protected/static")
    @sanic_jwt.protected(redirect_on_fail=True)
    async def my_protected_static(request):
        return text("", status=200)

    @sanic_app.route("/unprotected")
    async def my_unprotected_goto(request):
        return text("unprotected content", status=200)

    _, response = sanic_app.test_client.get("/protected/static")

    assert response.status == 200 and response.text == "unprotected content"


def test_authenticated_redirect(app_with_retrieve_user):
    sanic_app, sanic_jwt = app_with_retrieve_user
    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    sanic_app.router.reset()

    @sanic_app.route("/protected/static")
    @sanic_jwt.protected(redirect_on_fail=True)
    async def my_protected_static(request):
        return text("protected content", status=200)

    @sanic_app.route("/unprotected")
    async def my_unprotected_goto(request):
        return text("unprotected content", status=200)

    access_token = response.json.get(
        sanic_jwt.config.access_token_name(), None
    )

    _, response = sanic_app.test_client.get(
        "/protected/static",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 200 and response.text == "protected content"
