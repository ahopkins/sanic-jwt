import jwt
# import pytest

from sanic import Sanic
from sanic.response import json
from sanic_jwt import exceptions
from sanic_jwt import initialize
from sanic_jwt.decorators import protected
from sanic.views import HTTPMethodView


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def to_dict(self):
        properties = [
            'user_id',
            'username',
        ]
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


class PublicView(HTTPMethodView):
    def get(self, request):
        return json({"hello": "world"})


class ProtectedView(HTTPMethodView):
    decorators = [protected]

    async def get(self, request):
        return json({"protected": True})


app.add_route(PublicView.as_view(), '/')
app.add_route(ProtectedView.as_view(), '/protected')


class TestEndpointsCBV(object):
    def test_unprotected(self):
        _, response = app.test_client.get('/')
        assert response.status == 200

    def test_protected(self):
        _, response = app.test_client.get('/protected')
        assert response.status == 401

    def test_auth_invalid_method(self):
        _, response = app.test_client.get('/auth')
        assert response.status == 405

    def test_auth_proper_credentials(self):
        _, response = app.test_client.post('/auth', json={
            'username': 'user1',
            'password': 'abcxyz'
        })

        access_token = response.json.get(
            app.config.SANIC_JWT_ACCESS_TOKEN_NAME, None)
        payload = jwt.decode(access_token, app.config.SANIC_JWT_SECRET)

        assert response.status == 200
        assert access_token is not None
        assert isinstance(payload, dict)
        assert app.config.SANIC_JWT_USER_ID in payload
        assert 'exp' in payload

        _, response = app.test_client.get('/protected', headers={
            'Authorization': 'Bearer {}'.format(access_token)
        })
        assert response.status == 200

    # def test_auth_verify_missing_token(self):
    # with pytest.raises(exceptions.MissingAuthorizationHeader):
    # _, response = app.test_client.get('/auth/verify')
    # assert response.status == 200

    # def test_auth_refresh_not_enabled(self):
    #     with pytest.raises(exceptions.MissingAuthorizationHeader):
    #         _, response = app.test_client.post('/auth/refresh')
