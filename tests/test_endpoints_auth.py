import jwt
from sanic import Sanic
from sanic.response import json
from sanic_jwt import exceptions
from sanic_jwt import initialize
from sanic_jwt.decorators import protected


class User(object):
    def __init__(self, id, username, password):
        self.user_id = id
        self.username = username
        self.password = password

    def __str__(self):
        return "User(id='%s')" % self.id

    def to_dict(self):
        properties = ['user_id', 'username', ]
        return {prop: getattr(self, prop, None) for prop in properties}


users = [
    User(1, 'user1', 'abcxyz'),
    User(2, 'user2', 'abcxyz'),
]

username_table = {u.username: u for u in users}
# userid_table = {u.user_id: u for u in users}


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
)


@app.route("/")
async def helloworld(request):
    return json({"hello": "world"})


@app.route("/protected")
@protected()
async def protected(request):
    return json({"protected": True})


_, response = app.test_client.post('/auth', json={
    'username': 'user1',
    'password': 'abcxyz'
})

access_token = response.json.get(app.config.SANIC_JWT_ACCESS_TOKEN_NAME, None)
payload = jwt.decode(access_token, app.config.SANIC_JWT_SECRET)


class TestEndpointsAuth(object):
    def dispatch(self, path, method):
        header_token = '{} {}'.format(app.config.SANIC_JWT_AUTHORIZATION_HEADER_PREFIX, access_token)
        method = getattr(app.test_client, method)
        request, response = method(path, headers={
            app.config.SANIC_JWT_AUTHORIZATION_HEADER: header_token
        })
        return request, response

    def get(self, path):
        return self.dispatch(path, 'get')

    def test_verify_token(self):
        _, response = self.get('/auth/verify')

        assert response.status == 200
        assert response.json.get('valid') is True
