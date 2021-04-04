from sanic import Sanic
from sanic_jwt import exceptions
from sanic_jwt import Initialize
import jwt


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


async def generate_refresh_token():
    app = Sanic.get_app("myapp")
    payload = {}
    with app.ctx.auth.override(expiration_delta=60 * 60 * 24):
        payload = await app.ctx.auth.add_claims(payload, None)
    secret = await app.ctx.auth._get_secret(payload=payload, encode=True)
    algorithm = app.ctx.auth._get_algorithm()
    access_token = jwt.encode(payload, secret, algorithm=algorithm)
    return access_token


async def retrieve_refresh_token(request, user_id):
    refresh_token = request.json["refresh_token"]
    if await app.ctx.auth.verify_token(refresh_token):
        return refresh_token
    return None


def store_refresh_token(*args, **kwargs):
    ...


def retrieve_user(request, payload):
    return userid_table.get(payload["user_id"])


app = Sanic("myapp")
Initialize(
    app,
    authenticate=authenticate,
    generate_refresh_token=generate_refresh_token,
    refresh_token_enabled=True,
    retrieve_user=retrieve_user,
    retrieve_refresh_token=retrieve_refresh_token,
    store_refresh_token=store_refresh_token,
)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8888, debug=True)
