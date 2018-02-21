import binascii
import os

from sanic import Sanic
from sanic.response import json

import pytest
from sanic_jwt import Initialize
from sanic_jwt import exceptions
from sanic_jwt.decorators import protected


class User(object):

    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    async def to_dict(self):
        return {
            'user_id': hex(self.id),
            'username': self.username
        }

    @property
    def user_id(self):
        raise Exception('you shall not call me')


users = [
    User(1, 'user1', 'abcxyz'),
]


@pytest.yield_fixture
def app_with_async_methods():

    cache = {}

    async def authenticate(request, *args, **kwargs):
        username = request.json.get('username', None)
        password = request.json.get('password', None)

        if not username or not password:
            raise exceptions.AuthenticationFailed(
                "Missing username or password.")

        user = None

        for u in users:
            if u.username == username:
                user = u
                break

        if user is None:
            raise exceptions.AuthenticationFailed("User not found.")

        if password != user.password:
            raise exceptions.AuthenticationFailed("Password is incorrect.")

        return user

    async def store_refresh_token(user_id, refresh_token, *args, **kwargs):
        assert user_id == '0x1'
        key = 'refresh_token_{user_id}'.format(user_id=user_id)
        cache[key] = refresh_token
        print('key', key)
        print('refresh_token (stored):', refresh_token)

    async def retrieve_refresh_token(user_id, *args, **kwargs):
        assert user_id == '0x1'
        key = 'refresh_token_{user_id}'.format(user_id=user_id)
        print('key', key)
        return cache.get(key, None)

    async def retrieve_user(request, payload, *args, **kwargs):
        if payload:
            user_id = payload.get('user_id', None)
            assert user_id == '0x1'
            if user_id is not None:
                for u in users:
                    if u.id == int(user_id, base=16):
                        return u
        else:
            return None

    secret = str(binascii.hexlify(os.urandom(32)), 'utf-8')

    sanic_app = Sanic()
    sanicjwt = Initialize(sanic_app,
                          authenticate=authenticate,
                          store_refresh_token=store_refresh_token,
                          retrieve_refresh_token=retrieve_refresh_token,
                          retrieve_user=retrieve_user,
                          refresh_token_enabled=True,
                          secret=secret)

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    yield (sanic_app, sanicjwt)


class TestEndpointsAsync(object):

    @pytest.yield_fixture
    def authenticated_response(self, app_with_async_methods):
        app, sanicjwt = app_with_async_methods
        _, response = app.test_client.post(
            '/auth', json={
                'username': 'user1',
                'password': 'abcxyz'
            })
        assert response.status == 200
        yield response

    def test_root_endpoint(self, app_with_async_methods):
        app, _ = app_with_async_methods
        _, response = app.test_client.get('/')
        assert response.status == 200
        assert response.json.get('hello') == 'world'

    def test_protected_endpoint(self, app_with_async_methods,
                                authenticated_response):
        app, sanicjwt = app_with_async_methods
        access_token = authenticated_response.json.get(
            sanicjwt.config.access_token_name, None)

        _, response = app.test_client.get(
            '/protected',
            headers={
                'Authorization': 'Bearer {}'.format(access_token)
            })

        assert response.status == 200
        assert response.json.get('protected') is True

    def test_me_endpoint(self, app_with_async_methods,
                         authenticated_response):
        app, sanicjwt = app_with_async_methods
        access_token = authenticated_response.json.get(
            sanicjwt.config.access_token_name, None)

        _, response = app.test_client.get(
            '/auth/me',
            headers={
                'Authorization': 'Bearer {}'.format(access_token)
            })

        assert response.status == 200
        assert response.json.get('me').get('user_id') == '0x1'

    def test_refresh_token_async(self, app_with_async_methods,
                                 authenticated_response):
        app, sanicjwt = app_with_async_methods
        access_token = authenticated_response.json.get(
            sanicjwt.config.access_token_name, None)
        refresh_token = authenticated_response.json.get(
            sanicjwt.config.refresh_token_name, None)

        _, response = app.test_client.post(
            '/auth/refresh',
            headers={'Authorization': 'Bearer {}'.format(access_token)},
            json={
                sanicjwt.config.refresh_token_name: refresh_token
            })

        assert response.json is not None
        assert sanicjwt.config.access_token_name \
            in response.json

        new_access_token = response.json.get(
            sanicjwt.config.access_token_name, None)

        assert response.status == 200
        assert new_access_token is not None
        assert response.json.get(
            sanicjwt.config.refresh_token_name,
            None) is None  # there is no new refresh token
        assert \
            sanicjwt.config.refresh_token_name \
            not in response.json
