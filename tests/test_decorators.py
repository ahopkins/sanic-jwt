from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.response import json
from sanic_jwt import Initialize
from sanic_jwt.decorators import protected
from sanic_jwt.decorators import scoped


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
