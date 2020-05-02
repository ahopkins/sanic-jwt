from datetime import datetime, timedelta

from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.response import json

import jwt
from freezegun import freeze_time
from sanic_jwt import Initialize
from sanic_jwt.decorators import protected


async def authenticate(request, *args, **kwargs):
    return {"user_id": 1, "scopes": "user"}


async def my_scope_extender(user, *args, **kwargs):
    return user.get("scopes")


def test_decorators_override_configuration_defaults():
    blueprint = Blueprint("Test")

    app = Sanic("sanic-jwt-test")

    sanicjwt = Initialize(
        blueprint,
        app=app,
        authenticate=authenticate,
        scopes_enabled=True,
        retrieve_user=authenticate,
        add_scopes_to_payload=my_scope_extender,
    )

    @blueprint.get("/protected")
    @protected(blueprint, verify_exp=False)
    def protected_hello_world(request):
        return json({"message": "hello world"})

    @blueprint.route("/scoped")
    @sanicjwt.scoped("user", authorization_header="foobar")
    async def scoped_endpoint(request):
        return json({"scoped": True})

    app.blueprint(blueprint, url_prefix="/test")

    _, response = app.test_client.post(
        "/test/auth", json={"username": "user1", "password": "abcxyz"}
    )

    access_token = response.json.get(sanicjwt.config.access_token_name(), None)

    payload = jwt.decode(
        access_token,
        sanicjwt.config.secret(),
        algorithms=sanicjwt.config.algorithm(),
    )
    exp = payload.get("exp", None)

    assert "exp" in payload

    exp = datetime.utcfromtimestamp(exp)

    with freeze_time(datetime.utcnow() + timedelta(seconds=(60 * 35))):
        assert isinstance(exp, datetime)
        assert datetime.utcnow() > exp

        _, response = app.test_client.get(
            "/test/protected",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200

    _, response = app.test_client.get(
        "/test/scoped", headers={"FudgeBar": "Bearer {}".format(access_token)}
    )

    assert response.status == 401
    assert "Authorization header not present." in response.json.get("reasons")
    assert response.json.get("exception") == "Unauthorized"

    _, response = app.test_client.get(
        "/test/scoped", headers={"Foobar": "Bear {}".format(access_token)}
    )

    assert response.status == 401
    assert "Authorization header is invalid." in response.json.get("reasons")
    assert response.json.get("exception") == "Unauthorized"

    _, response = app.test_client.get(
        "/test/scoped", headers={"Foobar": "Bearer {}".format(access_token)}
    )

    assert response.status == 200
