from sanic import Sanic
from sanic.response import json
from sanic_jwt import exceptions
from sanic_jwt import initialize
from sanic_jwt.decorators import protected
from sanic_jwt.decorators import scoped


class User:
    def __init__(self, id, username, password, scopes):
        self.user_id = id
        self.username = username
        self.password = password
        self.scopes = scopes

    def __repr__(self):
        return "User(id='{}')".format(self.user_id)

    def to_dict(self):
        return {"user_id": self.user_id, "username": self.username}


users = [
    User(1, "user1", "abcxyz", ["user"]),
    User(2, "user2", "abcxyz", ["user", "admin"]),
    User(3, "user3", "abcxyz", ["user:read"]),
    User(4, "user4", "abcxyz", ["client1"]),
]

username_table = {u.username: u for u in users}
userid_table = {u.user_id: u for u in users}


async def authenticate(request, *args, **kwargs):
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    if not username or not password:
        raise exceptions.AuthenticationFailed("Missing username or password.")

    user = username_table.get(username, None)
    if user is None:
        raise exceptions.AuthenticationFailed("User not found.")

    if password != user.password:
        raise exceptions.AuthenticationFailed("Password is incorrect.")

    return user


async def retrieve_user(request, payload, *args, **kwargs):
    if payload:
        user_id = payload.get("user_id", None)
        if user_id is not None:
            return userid_table.get("user_id")

    else:
        return None


async def my_scope_extender(user, *args, **kwargs):
    return user.scopes


app = Sanic()
app.config.SANIC_JWT_HANDLER_PAYLOAD_SCOPES = my_scope_extender
initialize(app, authenticate=authenticate, retrieve_user=retrieve_user)
# initialize(app, authenticate=authenticate, retrieve_user=retrieve_user, add_scopes_to_payload=my_scope_extender)


@app.route("/")
async def test(request):
    return json({"hello": "world"})


@app.route("/protected")
@protected()
async def protected_route(request):
    return json({"protected": True, "scoped": False})


@app.route("/protected/scoped/1")
@protected()
@scoped("user")
async def protected_route1(request):
    return json({"protected": True, "scoped": True})


@app.route("/protected/scoped/2")
@protected()
@scoped("user:read")
async def protected_route2(request):
    return json({"protected": True, "scoped": True})


@app.route("/protected/scoped/3")
@protected()
@scoped(["user", "admin"])
async def protected_route3(request):
    return json({"protected": True, "scoped": True})


@app.route("/protected/scoped/4")
@protected()
@scoped(["user", "admin"], False)
async def protected_route4(request):
    return json({"protected": True, "scoped": True})


@app.route("/protected/scoped/5")
@scoped("user")
async def protected_route5(request):
    return json({"protected": True, "scoped": True})


@app.route("/protected/scoped/6/<id>")
@scoped(lambda *args, **kwargs: "user")
async def protected_route6(request, id):
    return json({"protected": True, "scoped": True})


def client_id_scope(request, *args, **kwargs):
    return "client" + kwargs.get("id")


@app.route("/protected/scoped/7/<id>")
@scoped(client_id_scope)
async def protected_route7(request, id):
    return json({"protected": True, "scoped": True})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8888)
