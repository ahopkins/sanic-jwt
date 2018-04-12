import binascii
import os

from sanic import Sanic
from sanic.response import json

import jwt
import pytest
from sanic_jwt import Initialize
from sanic_jwt import protected


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

    secret = str(binascii.hexlify(os.urandom(32)), 'utf-8')

    sanic_app = Sanic()
    sanicjwt = Initialize(sanic_app,
                          authenticate=authenticate,
                          store_refresh_token=store_refresh_token,
                          retrieve_refresh_token=retrieve_refresh_token,
                          retrieve_user=retrieve_user,
                          cookie_set=True,
                          cookie_strict=True,
                          refresh_token_enabled=True,
                          access_token_name='jwt_access_token',
                          refresh_token_name='jwt_refresh_token',
                          cookie_access_token_name='jwt_access_token',
                          cookie_refresh_token_name='jwt_refresh_token',
                          secret=secret,)

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    yield (sanic_app, sanicjwt)


class TestEndpointsCookies(object):

    @pytest.yield_fixture
    def authenticated_response(self, app_with_refresh_token):
        sanic_app, sanicjwt = app_with_refresh_token
        _, response = sanic_app.test_client.post(
            '/auth', json={
                'username': 'user1',
                'password': 'abcxyz'
            })
        assert response.status == 200
        yield response

    def test_authenticate_and_read_response_cookie(
            self, app_with_refresh_token, authenticated_response):
        _, sanicjwt = app_with_refresh_token
        key = sanicjwt.config.cookie_access_token_name()
        # print(key)
        # print(authenticated_response.cookies.values())
        access_token_from_cookie = authenticated_response.cookies.get(key,
                                                                      None)

        assert access_token_from_cookie is not None

        access_token_from_cookie = access_token_from_cookie.value
        access_token_from_json = authenticated_response.json.get(
            sanicjwt.config.access_token_name(), None)

        assert access_token_from_cookie is not None
        assert access_token_from_json is not None

        payload_cookie = jwt.decode(
            access_token_from_cookie,
            sanicjwt.config.secret())
        payload_json = jwt.decode(
            access_token_from_json,
            sanicjwt.config.secret())

        assert access_token_from_json is not None
        assert isinstance(payload_json, dict)
        assert isinstance(payload_cookie, dict)
        assert sanicjwt.config.user_id() in payload_json
        assert sanicjwt.config.user_id() in payload_cookie

    def test_using_token_as_cookie(self, app_with_refresh_token,
                                   authenticated_response):
        sanic_app, sanicjwt = app_with_refresh_token
        key = sanicjwt.config.cookie_access_token_name()
        access_token_from_cookie = \
            authenticated_response.cookies.get(key).value
        payload_cookie = jwt.decode(
            access_token_from_cookie,
            sanicjwt.config.secret())

        assert isinstance(payload_cookie, dict)
        assert \
            sanicjwt.config.user_id() in payload_cookie

        _, response = sanic_app.test_client.get(
            '/auth/me',
            cookies={
                sanicjwt.config.cookie_access_token_name():
                    access_token_from_cookie
            })

        assert 'me' in response.json
        assert response.json.get('me') is not None
        assert sanicjwt.config.user_id() in response.json.get('me')

        user_id_from_me = response.json.get('me').get(
            sanicjwt.config.user_id()
        )
        user_id_from_payload_cookie = payload_cookie.get(
            sanicjwt.config.user_id())

        assert response.status == 200
        assert user_id_from_me == user_id_from_payload_cookie

    def test_using_token_as_header_strict(self, app_with_refresh_token,
                                          authenticated_response):
        sanic_app, sanicjwt = app_with_refresh_token
        key = sanicjwt.config.cookie_access_token_name()
        access_token_from_cookie = \
            authenticated_response.cookies.get(key).value
        payload_cookie = jwt.decode(
            access_token_from_cookie,
            sanicjwt.config.secret())

        assert isinstance(payload_cookie, dict)
        assert \
            sanicjwt.config.user_id() in payload_cookie

        _, response = sanic_app.test_client.get(
            '/auth/me',
            headers={
                'Authorization': 'Bearer {}'.format(access_token_from_cookie)
            })

        assert response.status == 200
        assert response.json.get('me', {}) is None

        _, response = sanic_app.test_client.get(
            '/protected',
            headers={
                'Authorization': 'Bearer {}'.format(access_token_from_cookie)
            })

        assert response.status == 401

        _, response = sanic_app.test_client.get(
            '/auth/verify',
            headers={
                'Authorization': 'Bearer {}'.format(access_token_from_cookie)
            })

        _, response = sanic_app.test_client.get(
            '/protected',
            cookies={
                sanicjwt.config.cookie_access_token_name():
                    access_token_from_cookie
            })

        assert response.status == 200
        assert response.json.get('protected')

    def test_using_token_as_header_not_strict(self, app_with_refresh_token,
                                              authenticated_response):
        sanic_app, sanicjwt = app_with_refresh_token
        sanicjwt.config.cookie_strict.update(False)
        sanic_app.auth.config.cookie_strict.update(False)

        key = sanicjwt.config.cookie_access_token_name()
        access_token_from_cookie = \
            authenticated_response.cookies.get(key).value
        payload_cookie = jwt.decode(
            access_token_from_cookie,
            sanicjwt.config.secret())

        assert isinstance(payload_cookie, dict)
        assert \
            sanicjwt.config.user_id() in payload_cookie

        _, response = sanic_app.test_client.get(
            '/auth/me',
            headers={
                'Authorization': 'Bearer {}'.format(access_token_from_cookie)
            })

        assert response.status == 200
        assert response.json.get('me') is not None
        assert response.json.get('me').get(
            sanicjwt.config.user_id()
        ) == payload_cookie.get(
            sanicjwt.config.user_id())

        _, response = sanic_app.test_client.get(
            '/protected',
            headers={
                'Authorization': 'Bearer {}'.format(access_token_from_cookie)
            })

        assert response.status == 200

        _, response = sanic_app.test_client.get(
            '/auth/verify',
            headers={
                'Authorization': 'Bearer {}'.format(access_token_from_cookie)
            })

        _, response = sanic_app.test_client.get(
            '/protected',
            headers={
                'Authorization': 'Bearer {}'.format(access_token_from_cookie)
            })

        assert response.status == 200
        assert response.json.get('protected')

    def test_refresh_token_with_cookies_strict(self, app_with_refresh_token,
                                               authenticated_response):
        sanic_app, sanicjwt = app_with_refresh_token
        sanicjwt.config.debug.update(True)
        sanicjwt.config.cookie_strict.update(True)
        sanic_app.auth.config.cookie_strict.update(True)

        access_token = authenticated_response.json.get(
            sanicjwt.config.access_token_name(), None)
        refresh_token = authenticated_response.json.get(
            sanicjwt.config.cookie_refresh_token_name(),
            None)

        _, response = sanic_app.test_client.post(
            '/auth/refresh',
            cookies={
                sanicjwt.config.cookie_access_token_name():
                    access_token,
                sanicjwt.config.cookie_refresh_token_name():
                    refresh_token,
            })

        assert response.status == 200
        assert response.json is not None

        new_access_token = response.json.get(
            sanicjwt.config.access_token_name(), None)

        assert new_access_token is not None
        assert response.json.get(
            sanicjwt.config.cookie_refresh_token_name(),
            None) is None  # there is no new refresh token
        assert \
            sanicjwt.config.cookie_refresh_token_name() \
            not in response.json

        _, response = sanic_app.test_client.post(
            '/auth/refresh',
            json={
                sanicjwt.config.cookie_refresh_token_name():
                    refresh_token
            },
            headers={
                'Authorization': 'Bearer {}'.format(new_access_token)
            })

        assert response.status == 400

    def test_refresh_token_with_cookies_not_strict(
            self, app_with_refresh_token, authenticated_response):
        sanic_app, sanicjwt = app_with_refresh_token
        sanicjwt.config.cookie_strict.update(False)
        sanic_app.auth.config.cookie_strict.update(False)

        access_token = authenticated_response.json.get(
            sanicjwt.config.access_token_name(), None)
        refresh_token = authenticated_response.json.get(
            sanicjwt.config.cookie_refresh_token_name(),
            None)

        _, response = sanic_app.test_client.post(
            '/auth/refresh',
            json={
                sanicjwt.config.cookie_refresh_token_name():
                    refresh_token
            },
            headers={
                'Authorization': 'Bearer {}'.format(access_token)
            })

        assert response.status == 200
        assert response.json.get(
            sanicjwt.config.cookie_refresh_token_name(),
            None) is None  # there is no new refresh token
        assert \
            sanicjwt.config.cookie_refresh_token_name() \
            not in response.json
