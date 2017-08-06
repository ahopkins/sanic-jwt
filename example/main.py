from sanic import Sanic
from sanic.response import json
from aoiklivereload import LiveReloader
from sanic_jwt.decorators import protected
# from sanic_jwt.auth_bp import bp as sanic_jwt_auth_bp
from sanic_jwt import initialize, exceptions


reloader = LiveReloader()
reloader.start_watcher_thread()


def authenticate(request, *args, **kwargs):
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if not username or not password:
        raise exceptions.AuthenticationFailed("Missing username or password.")

    user = username_table.get(username, None)
    if user is None:
        raise exceptions.AuthenticationFailed("User not found.")

    if password != user.password:
        raise exceptions.AuthenticationFailed("Password is incorrect.")

    return user


app = Sanic()
initialize(app, authenticate)


class User(object):
    def __init__(self, id, username, password):
        setattr(self, app.config.SANIC_JWT_USER_ID, id)
        self.username = username
        self.password = password

    def __str__(self):
        return "User(id='%s')" % self.id


users = [
    User(1, 'user1', 'abcxyz'),
    User(2, 'user2', 'abcxyz'),
]

username_table = {u.username: u for u in users}
userid_table = {getattr(u, app.config.SANIC_JWT_USER_ID): u for u in users}


@app.route("/")
async def test(request):
    return json({"hello": "world"})


@app.route("/protected")
@protected()
async def test(request):
    return json({"protected": True})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
