from sanic import Sanic
from sanic.response import json
from sanic_jwt import exceptions
from sanic_jwt import Initialize
from sanic_jwt import protected
from sanic_jwt.decorators import inject_user


class User:
    def __init__(self, id, username, password):
        self.user_id = id
        self.username = username
        self.password = password

    def __repr__(self):
        return "User(id='{}')".format(self.user_id)

    def to_dict(self):
        return {"user_id": self.user_id, "username": self.username}


users = [User(1, "user1", "abcxyz"), User(2, "user2", "abcxyz")]

username_table = {u.username: u for u in users}
userid_table = {u.user_id: u for u in users}


async def retrieve_user(request, *args, **kwargs):
    payload = await request.app.auth.extract_payload(request)
    if not payload or "user_id" not in payload:
        return {}

    user_id = payload.get("user_id")
    user = userid_table.get(user_id)
    return user.to_dict()


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


app = Sanic(__name__)
sanic_jwt = Initialize(
    app, authenticate=authenticate, retrieve_user=retrieve_user
)


@app.route("/hello")
async def test(request):
    return json({"hello": "world"})


@app.route("/protected")
@protected()
async def protected(request):
    return json({"protected": True})


@app.route("/protected_user")
@sanic_jwt.protected()
@sanic_jwt.inject_user()
async def my_protected_user(request, user):
    return json({"user": user})


@app.route("/unprotected_user")
@inject_user()
async def my_unprotected_user(request, user):
    return json({"user": user})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8888, auto_reload=True)
