import binascii
import os

from sanic import Sanic
from sanic.response import json

import pytest
from sanic_jwt import initialize
from sanic_jwt import exceptions
from sanic_jwt.decorators import protected


@pytest.yield_fixture
def app_with_sync_methods(users):

    cache = {}

    def authenticate(request, *args, **kwargs):
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

    def store_refresh_token(user_id, refresh_token, *args, **kwargs):
        key = 'refresh_token_{user_id}'.format(user_id=user_id)
        cache[key] = refresh_token

    def retrieve_refresh_token(user_id, *args, **kwargs):
        key = 'refresh_token_{user_id}'.format(user_id=user_id)
        return cache.get(key, None)

    def retrieve_user(request, payload, *args, **kwargs):
        if payload:
            user_id = payload.get('user_id', None)
            if user_id is not None:
                for u in users:
                    if u.user_id == user_id:
                        return u
        else:
            return None

    sanic_app = Sanic()
    initialize(
        sanic_app,
        authenticate=authenticate,
        store_refresh_token=store_refresh_token,
        retrieve_refresh_token=retrieve_refresh_token,
        retrieve_user=retrieve_user)

    sanic_app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED = True
    sanic_app.config.SANIC_JWT_SECRET = str(
        binascii.hexlify(os.urandom(32)), 'utf-8')

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    yield sanic_app


class TestEndpointsSync(object):

    @pytest.yield_fixture
    def authenticated_response(self, app_with_sync_methods):
        _, response = app_with_sync_methods.test_client.post(
            '/auth', json={
                'username': 'user1',
                'password': 'abcxyz'
            })
        assert response.status == 200
        yield response

    def test_root_endpoint(self, app_with_sync_methods):
        _, response = app_with_sync_methods.test_client.get('/')
        assert response.status == 200
        assert response.json.get('hello') == 'world'

    def test_protected_endpoint(self, app_with_sync_methods,
                                authenticated_response):

        access_token = authenticated_response.json.get(
            app_with_sync_methods.config.SANIC_JWT_ACCESS_TOKEN_NAME, None)

        _, response = app_with_sync_methods.test_client.get(
            '/protected',
            headers={
                'Authorization': 'Bearer {}'.format(access_token)
            })

        assert response.status == 200
        assert response.json.get('protected') is True

    def test_me_endpoint(self, app_with_sync_methods,
                         authenticated_response):

        access_token = authenticated_response.json.get(
            app_with_sync_methods.config.SANIC_JWT_ACCESS_TOKEN_NAME, None)

        _, response = app_with_sync_methods.test_client.get(
            '/auth/me',
            headers={
                'Authorization': 'Bearer {}'.format(access_token)
            })

        assert response.status == 200

    def test_refresh_token_sunc(self, app_with_sync_methods,
                                authenticated_response):

        access_token = authenticated_response.json.get(
            app_with_sync_methods.config.SANIC_JWT_ACCESS_TOKEN_NAME, None)
        refresh_token = authenticated_response.json.get(
            app_with_sync_methods.config.SANIC_JWT_REFRESH_TOKEN_NAME, None)

        _, response = app_with_sync_methods.test_client.post(
            '/auth/refresh',
            headers={'Authorization': 'Bearer {}'.format(access_token)},
            json={
                app_with_sync_methods.config.
                SANIC_JWT_REFRESH_TOKEN_NAME:
                    refresh_token
            })

        new_access_token = response.json.get(
            app_with_sync_methods.config.SANIC_JWT_ACCESS_TOKEN_NAME, None)

        assert response.status == 200
        assert new_access_token is not None
        assert response.json.get(
            app_with_sync_methods.config.SANIC_JWT_REFRESH_TOKEN_NAME,
            None) is None  # there is no new refresh token
        assert \
            app_with_sync_methods.config.SANIC_JWT_REFRESH_TOKEN_NAME \
            not in response.json
