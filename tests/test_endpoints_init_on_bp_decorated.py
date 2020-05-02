from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.response import json

from sanic_jwt import Initialize


async def authenticate(request, *args, **kwargs):
    return {"user_id": 1}


blueprint = Blueprint("Test")
app = Sanic("sanic-jwt-test")
sanicjwt = Initialize(blueprint, app=app, authenticate=authenticate)


@blueprint.get("/", strict_slashes=True)
@sanicjwt.protected()
def protected_hello_world(request):
    return json({"message": "hello world"})


@blueprint.get("/user/<id>", strict_slashes=True)
@sanicjwt.protected(authorization_header="foobar")
def protected_user(request, id):
    return json({"user": id})


@blueprint.route("/scoped_empty")
@sanicjwt.scoped("something")
async def scoped(request):
    return json({"scoped": True})


app.blueprint(blueprint, url_prefix="/test")


def test_protected_blueprint():
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

    _, response = app.test_client.get(
        "/test/user/1",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 401
    assert response.json.get("exception") == "Unauthorized"
    assert "Authorization header not present." in response.json.get("reasons")

    _, response = app.test_client.get(
        "/test/user/1", headers={"Foobar": "Bearer {}".format(access_token)}
    )

    assert response.status == 200
    assert response.json.get("user") == "1"


def test_scoped_empty():
    _, response = app.test_client.get("/test/scoped_empty")
    assert response.status == 401
    assert response.json.get("exception") == "Unauthorized"
    assert "Authorization header not present." in response.json.get("reasons")
