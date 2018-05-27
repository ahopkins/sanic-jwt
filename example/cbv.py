from sanic import Sanic
from sanic_jwt import exceptions
from sanic_jwt import initialize
from sanic.response import json
from sanic_jwt.decorators import protected
from sanic.views import HTTPMethodView


class User:

    def __init__(self, id, username, password):
        self.user_id = id
        self.username = username
        self.password = password

    def __str__(self):
        return "User(id='%s')" % self.id

    def to_dict(self):
        return {"user_id": self.user_id}


users = [User(1, "user1", "abcxyz"), User(2, "user2", "abcxyz")]

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


app = Sanic()
initialize(app, authenticate=authenticate)


class PublicView(HTTPMethodView):

    def get(self, request):
        return json({"hello": "world"})


class ProtectedView(HTTPMethodView):
    decorators = [protected()]

    async def get(self, request):
        return json({"protected": True})


app.add_route(PublicView.as_view(), "/")
app.add_route(ProtectedView.as_view(), "/protected")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8888)
