from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.response import json
from sanic_jwt import Initialize
from sanic_jwt.decorators import protected

blueprint = Blueprint("Test")


@blueprint.get("/somewhere", strict_slashes=True)
@protected(blueprint)
def protected_hello_world(request):
    return json({"message": "hello world"})


@blueprint.get("/user/<id>", strict_slashes=True)
@protected(blueprint)
def protected_user(request, id):
    return json({"user": id})


async def authenticate(request, *args, **kwargs):
    return {"user_id": 1}


app = Sanic()


sanicjwt = Initialize(blueprint, app=app, authenticate=authenticate)

app.blueprint(blueprint, url_prefix="/test")


if __name__ == "__main__":
    print(app.router.routes_all)
    app.run(host="127.0.0.1", port=8888)
