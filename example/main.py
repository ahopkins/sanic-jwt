import csv
import os
from aoiklivereload import LiveReloader
from sanic import Sanic
from sanic.response import json
from sanic_jwt import exceptions
from sanic_jwt import initialize
from sanic_jwt.decorators import protected


reloader = LiveReloader()
reloader.start_watcher_thread()


def store_refresh_token(*args, **kwargs):
    user_id = kwargs.get('user_id')
    user = userid_table.get(user_id)
    refresh_token = kwargs.get('refresh_token')
    setattr(user, 'refresh_token', refresh_token)
    user.refresh_token = refresh_token

    save_users()


def retrieve_user(request, *args, **kwargs):
    if 'user_id' in kwargs:
        user_id = kwargs.get('user_id')
    else:
        if 'payload' in kwargs:
            payload = kwargs.get('payload')
        else:
            payload = request.app.auth.extract_payload(request)
        user_id = payload.get('user_id')
    user = userid_table.get(user_id)
    return user


def retrieve_refresh_token(request, *args, **kwargs):
    user = request.app.auth.retrieve_user(request, **kwargs)
    return user.refresh_token


async def authenticate(request, *args, **kwargs):
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
initialize(
    app,
    authenticate=authenticate,
    store_refresh_token=store_refresh_token,
    retrieve_refresh_token=retrieve_refresh_token,
    retrieve_user=retrieve_user,
)
app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED = True
app.config.SANIC_JWT_CLAIM_ISS = 'foo:bar'
app.config.SANIC_JWT_CLAIM_IAT = True
app.config.SANIC_JWT_CLAIM_NBF = True
app.config.SANIC_JWT_CLAIM_AUD = 'bar:foo'


class User(object):
    def __init__(self, id, username, password):
        setattr(self, app.config.SANIC_JWT_USER_ID, id)
        self.username = username
        self.password = password

    def __str__(self):
        return "User(id='%s')" % self.user_id

    def serialized(self):
        output = [
            getattr(self, app.config.SANIC_JWT_USER_ID),
            self.username,
            self.password,
            getattr(self, 'refresh_token', ''),
        ]
        return output


users = []
file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.csv')

with open(file_path, 'r') as file:
    reader = csv.reader(file)

    for line in reader:
        user = User(line[0], line[1], line[2])

        try:
            user.refresh_token = line[3]
        except IndexError:
            pass

        users.append(user)

username_table = {u.username: u for u in users}
userid_table = {getattr(u, app.config.SANIC_JWT_USER_ID): u for u in users}


def save_users():
    with open(file_path, 'w') as file:
        writer = csv.writer(file)
        for user in users:
            writer.writerow(user.serialized())


@app.route("/hello")
async def test(request):
    return json({"hello": "world"})


@app.route("/protected")
@protected()
async def protected(request):
    return json({"protected": True})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8888)
