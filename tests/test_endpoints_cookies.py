import binascii
import os

from sanic import Sanic
from sanic.response import json

import jwt
import pytest
from sanic_jwt import initialize
from sanic_jwt.decorators import protected


@pytest.yield_fixture
def app_with_refresh_token(users, authenticate):

    cache = {}

    async def store_refresh_token(user_id, refresh_token, *args, **kwargs):
        key = 'refresh_token_{user_id}'.format(user_id=user_id)
        cache[key] = refresh_token

    async def retrieve_refresh_token(user_id, *args, **kwargs):
        key = 'refresh_token_{user_id}'.format(user_id=user_id)
        return cache.get(key, None)

    async def retrieve_user(request, payload, *args, **kwargs):
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

    # configure app to use cookies
    sanic_app.config.SANIC_JWT_COOKIE_SET = True
    sanic_app.config.SANIC_JWT_COOKIE_STRICT = True  # default value
    sanic_app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED = True
    sanic_app.config.SANIC_JWT_ACCESS_TOKEN_NAME = 'jwt_access_token'
    sanic_app.config.SANIC_JWT_REFRESH_TOKEN_NAME = 'jwt_refresh_token'
    sanic_app.config.SANIC_JWT_COOKIE_REFRESH_TOKEN_NAME = \
        sanic_app.config.SANIC_JWT_REFRESH_TOKEN_NAME
    sanic_app.config.SANIC_JWT_COOKIE_ACCESS_TOKEN_NAME = \
        sanic_app.config.SANIC_JWT_ACCESS_TOKEN_NAME
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


class TestEndpointsCookies(object):

    @pytest.yield_fixture
    def authenticated_response(self, app_with_refresh_token):
        _, response = app_with_refresh_token.test_client.post(
            '/auth', json={
                'username': 'user1',
                'password': 'abcxyz'
            })
        assert response.status == 200
        yield response

    def test_authenticate_and_read_response_cookie(
            self, app_with_refresh_token, authenticated_response):

        key = app_with_refresh_token.config.SANIC_JWT_COOKIE_ACCESS_TOKEN_NAME
        access_token_from_cookie = authenticated_response.cookies.get(key,
                                                                      None)

        # for sanity sakes
        assert access_token_from_cookie is not None

        access_token_from_cookie = access_token_from_cookie.value
        access_token_from_json = authenticated_response.json.get(
            app_with_refresh_token.config.SANIC_JWT_ACCESS_TOKEN_NAME, None)
        payload_cookie = jwt.decode(
            access_token_from_cookie,
            app_with_refresh_token.config.SANIC_JWT_SECRET)
        payload_json = jwt.decode(
            access_token_from_json,
            app_with_refresh_token.config.SANIC_JWT_SECRET)

        assert access_token_from_json is not None
        assert isinstance(payload_json, dict)
        assert isinstance(payload_cookie, dict)
        assert \
            app_with_refresh_token.config.SANIC_JWT_USER_ID in payload_json
        assert \
            app_with_refresh_token.config.SANIC_JWT_USER_ID in payload_cookie

    def test_using_token_as_cookie(self, app_with_refresh_token,
                                   authenticated_response):

        key = app_with_refresh_token.config.SANIC_JWT_COOKIE_ACCESS_TOKEN_NAME
        access_token_from_cookie = \
            authenticated_response.cookies.get(key).value
        payload_cookie = jwt.decode(
            access_token_from_cookie,
            app_with_refresh_token.config.SANIC_JWT_SECRET)

        assert isinstance(payload_cookie, dict)
        assert \
            app_with_refresh_token.config.SANIC_JWT_USER_ID in payload_cookie

        _, response = app_with_refresh_token.test_client.get(
            '/auth/me',
            cookies={
                app_with_refresh_token.config.SANIC_JWT_COOKIE_ACCESS_TOKEN_NAME:
                    access_token_from_cookie
            })

        assert 'me' in response.json
        assert response.json.get('me') is not None
        assert app_with_refresh_token.config.SANIC_JWT_USER_ID in response.json.get('me')

        user_id_from_me = response.json.get('me').get(
            app_with_refresh_token.config.SANIC_JWT_USER_ID
        )
        user_id_from_payload_cookie = payload_cookie.get(
            app_with_refresh_token.config.SANIC_JWT_USER_ID)

        assert response.status == 200
        assert user_id_from_me == user_id_from_payload_cookie

    def test_using_token_as_header_strict(self, app_with_refresh_token,
                                          authenticated_response):

        key = app_with_refresh_token.config.SANIC_JWT_COOKIE_ACCESS_TOKEN_NAME
        access_token_from_cookie = \
            authenticated_response.cookies.get(key).value
        payload_cookie = jwt.decode(
            access_token_from_cookie,
            app_with_refresh_token.config.SANIC_JWT_SECRET)

        assert isinstance(payload_cookie, dict)
        assert \
            app_with_refresh_token.config.SANIC_JWT_USER_ID in payload_cookie

        _, response = app_with_refresh_token.test_client.get(
            '/auth/me',
            headers={
                'Authorization': 'Bearer {}'.format(access_token_from_cookie)
            })

        assert response.status == 200
        assert response.json.get('me', {}) is None

        _, response = app_with_refresh_token.test_client.get(
            '/protected',
            headers={
                'Authorization': 'Bearer {}'.format(access_token_from_cookie)
            })

        assert response.status == 401

        _, response = app_with_refresh_token.test_client.get(
            '/auth/verify',
            headers={
                'Authorization': 'Bearer {}'.format(access_token_from_cookie)
            })

        _, response = app_with_refresh_token.test_client.get(
            '/protected',
            cookies={
                app_with_refresh_token.config.SANIC_JWT_COOKIE_ACCESS_TOKEN_NAME:
                    access_token_from_cookie
            })

        assert response.status == 200
        assert response.json.get('protected')

    def test_using_token_as_header_not_strict(self, app_with_refresh_token,
                                              authenticated_response):

        app_with_refresh_token.config.SANIC_JWT_COOKIE_STRICT = False

        key = app_with_refresh_token.config.SANIC_JWT_COOKIE_ACCESS_TOKEN_NAME
        access_token_from_cookie = \
            authenticated_response.cookies.get(key).value
        payload_cookie = jwt.decode(
            access_token_from_cookie,
            app_with_refresh_token.config.SANIC_JWT_SECRET)

        assert isinstance(payload_cookie, dict)
        assert \
            app_with_refresh_token.config.SANIC_JWT_USER_ID in payload_cookie

        _, response = app_with_refresh_token.test_client.get(
            '/auth/me',
            headers={
                'Authorization': 'Bearer {}'.format(access_token_from_cookie)
            })

        assert response.status == 200
        assert response.json.get('me').get(
            app_with_refresh_token.config.SANIC_JWT_USER_ID
        ) == payload_cookie.get(
            app_with_refresh_token.config.SANIC_JWT_USER_ID)

        _, response = app_with_refresh_token.test_client.get(
            '/protected',
            headers={
                'Authorization': 'Bearer {}'.format(access_token_from_cookie)
            })

        assert response.status == 200

        _, response = app_with_refresh_token.test_client.get(
            '/auth/verify',
            headers={
                'Authorization': 'Bearer {}'.format(access_token_from_cookie)
            })

        _, response = app_with_refresh_token.test_client.get(
            '/protected',
            headers={
                'Authorization': 'Bearer {}'.format(access_token_from_cookie)
            })

        assert response.status == 200
        assert response.json.get('protected')

    def test_refresh_token_with_cookies_strict(self, app_with_refresh_token,
                                               authenticated_response):

        app_with_refresh_token.config.SANIC_JWT_COOKIE_STRICT = True

        access_token = authenticated_response.json.get(
            app_with_refresh_token.config.SANIC_JWT_ACCESS_TOKEN_NAME, None)
        refresh_token = authenticated_response.json.get(
            app_with_refresh_token.config.SANIC_JWT_COOKIE_REFRESH_TOKEN_NAME,
            None)

        _, response = app_with_refresh_token.test_client.post(
            '/auth/refresh',
            cookies={
                app_with_refresh_token.config.SANIC_JWT_COOKIE_ACCESS_TOKEN_NAME:
                    access_token,
                app_with_refresh_token.config.
                SANIC_JWT_COOKIE_REFRESH_TOKEN_NAME:
                    refresh_token,
            })

        new_access_token = response.json.get(
            app_with_refresh_token.config.SANIC_JWT_ACCESS_TOKEN_NAME, None)

        assert response.status == 200
        assert new_access_token is not None
        assert response.json.get(
            app_with_refresh_token.config.SANIC_JWT_COOKIE_REFRESH_TOKEN_NAME,
            None) is None  # there is no new refresh token
        assert \
            app_with_refresh_token.config.SANIC_JWT_COOKIE_REFRESH_TOKEN_NAME \
            not in response.json

        _, response = app_with_refresh_token.test_client.post(
            '/auth/refresh',
            json={
                app_with_refresh_token.config.
                SANIC_JWT_COOKIE_REFRESH_TOKEN_NAME:
                    refresh_token
            },
            headers={
                'Authorization': 'Bearer {}'.format(new_access_token)
            })

        assert response.status == 400

    def test_refresh_token_with_cookies_not_strict(
            self, app_with_refresh_token, authenticated_response):

        app_with_refresh_token.config.SANIC_JWT_COOKIE_STRICT = False

        access_token = authenticated_response.json.get(
            app_with_refresh_token.config.SANIC_JWT_ACCESS_TOKEN_NAME, None)
        refresh_token = authenticated_response.json.get(
            app_with_refresh_token.config.SANIC_JWT_COOKIE_REFRESH_TOKEN_NAME,
            None)

        _, response = app_with_refresh_token.test_client.post(
            '/auth/refresh',
            json={
                app_with_refresh_token.config.
                SANIC_JWT_COOKIE_REFRESH_TOKEN_NAME:
                    refresh_token
            },
            headers={
                'Authorization': 'Bearer {}'.format(access_token)
            })

        assert response.status == 200
        assert response.json.get(
            app_with_refresh_token.config.SANIC_JWT_COOKIE_REFRESH_TOKEN_NAME,
            None) is None  # there is no new refresh token
        assert \
            app_with_refresh_token.config.SANIC_JWT_COOKIE_REFRESH_TOKEN_NAME \
            not in response.json
