from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.response import json
from sanic_jwt import Initialize
from sanic_jwt.decorators import protected
from sanic_jwt.decorators import scoped

blueprint = Blueprint("Test")


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
async def scoped(request):
    return json({"scoped": True})


async def authenticate(request, *args, **kwargs):
    return {"user_id": 1}


app = Sanic()


sanicjwt = Initialize(blueprint, app=app, authenticate=authenticate)

app.blueprint(blueprint, url_prefix="/test")


def test_protected_blueprint():
    _, response = app.test_client.get("/test/")

    assert response.status == 401
    assert response.json.get("exception") == "Unauthorized"
    assert "Authorization header not present." in response.json.get('reasons')

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


def test_scoped_empty():
    _, response = app.test_client.get("/test/scoped_empty")
    assert response.status == 401
    assert response.json.get("exception") == "Unauthorized"
    assert "Authorization header not present." in response.json.get('reasons')
