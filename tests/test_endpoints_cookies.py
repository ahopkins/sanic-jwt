import binascii
import os
from datetime import datetime

import jwt
import pytest
from sanic import Sanic
from sanic.response import json

from sanic_jwt import Initialize, protected


@pytest.fixture
def app_with_refresh_token_and_cookie(users, authenticate):

    cache = {}

    async def store_refresh_token(user_id, refresh_token, *args, **kwargs):
        key = "refresh_token_{user_id}".format(user_id=user_id)
        cache[key] = refresh_token

    async def retrieve_refresh_token(user_id, *args, **kwargs):
        key = "refresh_token_{user_id}".format(user_id=user_id)
        return cache.get(key, None)

    async def retrieve_user(request, payload, *args, **kwargs):
        if payload:
            user_id = payload.get("user_id", None)
            if user_id is not None:
                for u in users:
                    if u.user_id == user_id:
                        return u

        else:
            return None

    secret = str(binascii.hexlify(os.urandom(32)), "utf-8")

    sanic_app = Sanic("sanic-jwt-test")
    sanicjwt = Initialize(
        sanic_app,
        authenticate=authenticate,
        store_refresh_token=store_refresh_token,
        retrieve_refresh_token=retrieve_refresh_token,
        retrieve_user=retrieve_user,
        cookie_set=True,
        cookie_strict=True,
        refresh_token_enabled=True,
        access_token_name="jwt_access_token",
        refresh_token_name="jwt_refresh_token",
        cookie_access_token_name="jwt_access_token",
        cookie_refresh_token_name="jwt_refresh_token",
        secret=secret,
    )

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    yield (sanic_app, sanicjwt)


class TestEndpointsCookies(object):
    @pytest.fixture
    def authenticated_response(self, app_with_refresh_token_and_cookie):
        sanic_app, sanicjwt = app_with_refresh_token_and_cookie
        _, response = sanic_app.test_client.post(
            "/auth", json={"username": "user1", "password": "abcxyz"}
        )
        assert response.status == 200
        yield response

    def test_authenticate_and_read_response_cookie(
        self, app_with_refresh_token_and_cookie, authenticated_response
    ):
        _, sanicjwt = app_with_refresh_token_and_cookie
        key = sanicjwt.config.cookie_access_token_name()

        access_token_from_cookie = authenticated_response.cookies.get(
            key, None
        )

        assert access_token_from_cookie is not None

        access_token_from_json = authenticated_response.json.get(
            sanicjwt.config.access_token_name()
        )

        assert access_token_from_cookie is not None
        assert access_token_from_json is not None

        payload_cookie = jwt.decode(
            access_token_from_cookie,
            sanicjwt.config.secret(),
            algorithms=sanicjwt.config.algorithm(),
        )
        payload_json = jwt.decode(
            access_token_from_json,
            sanicjwt.config.secret(),
            algorithms=sanicjwt.config.algorithm(),
        )

        assert access_token_from_json is not None
        assert isinstance(payload_json, dict)
        assert isinstance(payload_cookie, dict)
        assert sanicjwt.config.user_id() in payload_json
        assert sanicjwt.config.user_id() in payload_cookie

    def test_using_token_as_cookie(
        self, app_with_refresh_token_and_cookie, authenticated_response
    ):
        sanic_app, sanicjwt = app_with_refresh_token_and_cookie
        key = sanicjwt.config.cookie_access_token_name()
        access_token_from_cookie = authenticated_response.cookies.get(key)
        payload_cookie = jwt.decode(
            access_token_from_cookie,
            sanicjwt.config.secret(),
            algorithms=sanicjwt.config.algorithm(),
        )

        assert isinstance(payload_cookie, dict)
        assert sanicjwt.config.user_id() in payload_cookie

        _, response = sanic_app.test_client.get(
            "/auth/me",
            cookies={
                sanicjwt.config.cookie_access_token_name(): access_token_from_cookie
            },
        )

        assert "me" in response.json
        assert response.json.get("me") is not None
        assert sanicjwt.config.user_id() in response.json.get("me")

        user_id_from_me = response.json.get("me").get(
            sanicjwt.config.user_id()
        )
        user_id_from_payload_cookie = payload_cookie.get(
            sanicjwt.config.user_id()
        )

        assert response.status == 200
        assert user_id_from_me == user_id_from_payload_cookie

    def test_using_token_as_header_strict(
        self, app_with_refresh_token_and_cookie, authenticated_response
    ):
        sanic_app, sanicjwt = app_with_refresh_token_and_cookie
        key = sanicjwt.config.cookie_access_token_name()
        access_token_from_cookie = authenticated_response.cookies.get(key)
        payload_cookie = jwt.decode(
            access_token_from_cookie,
            sanicjwt.config.secret(),
            algorithms=sanicjwt.config.algorithm(),
        )

        assert isinstance(payload_cookie, dict)
        assert sanicjwt.config.user_id() in payload_cookie

        _, response = sanic_app.test_client.get(
            "/auth/me",
            headers={
                "Authorization": "Bearer {}".format(access_token_from_cookie)
            },
        )

        assert response.status == 401
        assert response.json.get("exception") == "Unauthorized"
        assert "Authorization cookie not present." in response.json.get(
            "reasons"
        )

        _, response = sanic_app.test_client.get(
            "/protected",
            headers={
                "Authorization": "Bearer {}".format(access_token_from_cookie)
            },
        )

        assert response.status == 401
        assert response.json.get("exception") == "Unauthorized"
        assert "Authorization cookie not present." in response.json.get(
            "reasons"
        )

        _, response = sanic_app.test_client.get(
            "/auth/verify",
            headers={
                "Authorization": "Bearer {}".format(access_token_from_cookie)
            },
        )

        assert response.status == 401
        assert response.json.get("exception") == "MissingAuthorizationCookie"
        assert "Authorization cookie not present." in response.json.get(
            "reasons"
        )

        _, response = sanic_app.test_client.get(
            "/auth/me",
            cookies={
                sanicjwt.config.cookie_access_token_name(): access_token_from_cookie
            },
        )

        assert response.status == 200
        assert response.json.get("me")

        _, response = sanic_app.test_client.get(
            "/protected",
            cookies={
                sanicjwt.config.cookie_access_token_name(): access_token_from_cookie
            },
        )

        assert response.status == 200
        assert response.json.get("protected")

    def test_using_token_as_header_not_strict(
        self, app_with_refresh_token_and_cookie, authenticated_response
    ):
        sanic_app, sanicjwt = app_with_refresh_token_and_cookie
        sanicjwt.config.cookie_strict.update(False)
        sanic_app.auth.config.cookie_strict.update(False)

        key = sanicjwt.config.cookie_access_token_name()
        access_token_from_cookie = authenticated_response.cookies.get(key)
        payload_cookie = jwt.decode(
            access_token_from_cookie,
            sanicjwt.config.secret(),
            algorithms=sanicjwt.config.algorithm(),
        )

        assert isinstance(payload_cookie, dict)
        assert sanicjwt.config.user_id() in payload_cookie

        _, response = sanic_app.test_client.get(
            "/auth/me",
            headers={
                "Authorization": "Bearer {}".format(access_token_from_cookie)
            },
        )

        assert response.status == 200
        assert response.json.get("me") is not None
        assert response.json.get("me").get(
            sanicjwt.config.user_id()
        ) == payload_cookie.get(sanicjwt.config.user_id())

        _, response = sanic_app.test_client.get(
            "/protected",
            headers={
                "Authorization": "Bearer {}".format(access_token_from_cookie)
            },
        )

        assert response.status == 200

        _, response = sanic_app.test_client.get(
            "/auth/verify",
            headers={
                "Authorization": "Bearer {}".format(access_token_from_cookie)
            },
        )

        _, response = sanic_app.test_client.get(
            "/protected",
            headers={
                "Authorization": "Bearer {}".format(access_token_from_cookie)
            },
        )

        assert response.status == 200
        assert response.json.get("protected")

    def test_refresh_token_with_cookies_strict(
        self, app_with_refresh_token_and_cookie, authenticated_response
    ):
        sanic_app, sanicjwt = app_with_refresh_token_and_cookie
        sanicjwt.config.debug.update(True)
        sanicjwt.config.cookie_strict.update(True)
        sanic_app.auth.config.cookie_strict.update(True)

        access_token = authenticated_response.json.get(
            sanicjwt.config.access_token_name(), None
        )
        refresh_token = authenticated_response.json.get(
            sanicjwt.config.cookie_refresh_token_name(), None
        )

        _, response = sanic_app.test_client.post(
            "/auth/refresh",
            cookies={
                sanicjwt.config.cookie_access_token_name(): access_token,
                sanicjwt.config.cookie_refresh_token_name(): refresh_token,
            },
        )

        assert response.status == 200
        assert response.json is not None

        new_access_token = response.json.get(
            sanicjwt.config.access_token_name(), None
        )

        assert new_access_token is not None
        assert (
            response.json.get(
                sanicjwt.config.cookie_refresh_token_name(), None
            )
            is None
        )  # there is no new refresh token
        assert sanicjwt.config.cookie_refresh_token_name() not in response.json

        sanicjwt.config.debug.update(False)
        _, response = sanic_app.test_client.post(
            "/auth/refresh",
            json={sanicjwt.config.cookie_refresh_token_name(): refresh_token},
            headers={"Authorization": "Bearer {}".format(new_access_token)},
        )

        assert response.status == 401
        assert response.json.get("exception") == "Unauthorized"
        assert "Authorization cookie not present." in response.json.get(
            "reasons"
        )

        sanicjwt.config.debug.update(True)
        _, response = sanic_app.test_client.post(
            "/auth/refresh",
            json={sanicjwt.config.cookie_refresh_token_name(): refresh_token},
            headers={"Authorization": "Bearer {}".format(new_access_token)},
        )

        assert response.status == 400
        assert response.json.get("exception") == "Unauthorized"
        assert "Authorization cookie not present." in response.json.get(
            "reasons"
        )

    def test_refresh_token_with_cookies_not_strict(
        self, app_with_refresh_token_and_cookie, authenticated_response
    ):
        sanic_app, sanicjwt = app_with_refresh_token_and_cookie
        sanicjwt.config.cookie_strict.update(False)
        sanic_app.auth.config.cookie_strict.update(False)

        access_token = authenticated_response.json.get(
            sanicjwt.config.access_token_name(), None
        )
        refresh_token = authenticated_response.json.get(
            sanicjwt.config.cookie_refresh_token_name(), None
        )

        _, response = sanic_app.test_client.post(
            "/auth/refresh",
            json={sanicjwt.config.cookie_refresh_token_name(): refresh_token},
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert (
            response.json.get(
                sanicjwt.config.cookie_refresh_token_name(), None
            )
            is None
        )  # there is no new refresh token
        assert sanicjwt.config.cookie_refresh_token_name() not in response.json

    def test_auth_verify_invalid_token(
        self, app_with_refresh_token_and_cookie
    ):
        sanic_app, sanicjwt = app_with_refresh_token_and_cookie

        _, response = sanic_app.test_client.get(
            "/auth/verify",
            cookies={sanicjwt.config.cookie_access_token_name(): ""},
        )
        assert response.status == 401
        assert response.json.get("exception") == "MissingAuthorizationCookie"
        assert "Authorization cookie not present." in response.json.get(
            "reasons"
        )


@pytest.mark.xfail(
    reason="Sanic does not yet allow for customizing the domain on the test_client"
)
def test_config_with_cookie_domain(users, authenticate):
    domain = "cookie.yum"
    sanic_app = Sanic("sanic-jwt-test")
    Initialize(
        sanic_app,
        authenticate=authenticate,
        cookie_set=True,
        cookie_domain=domain,
    )

    _, response = sanic_app.test_client.post(
        "/auth",
        json={"username": "user1", "password": "abcxyz"},
        raw_cookies=True,
    )

    cookie = response.raw_cookies.get("access_token")
    assert cookie.domain == domain


def test_config_with_cookie_path(users, authenticate):
    path = "/auth"
    sanic_app = Sanic("sanic-jwt-test")
    Initialize(
        sanic_app, authenticate=authenticate, cookie_set=True, cookie_path=path
    )

    _, response = sanic_app.test_client.post(
        "/auth",
        json={"username": "user1", "password": "abcxyz"},
        raw_cookies=True,
    )

    cookie = response.raw_cookies.get("access_token")
    assert cookie.path == path


def test_with_split_cookie(app):
    sanic_app, sanicjwt = app
    sanicjwt.config.cookie_set.update(True)
    sanicjwt.config.cookie_split.update(True)
    key = sanicjwt.config.cookie_access_token_name()
    sig_key = sanicjwt.config.cookie_split_signature_name()

    _, response = sanic_app.test_client.post(
        "/auth",
        json={"username": "user1", "password": "abcxyz"},
        raw_cookies=True,
    )
    token_cookie = response.raw_cookies.get(key)
    signature_cookie = response.raw_cookies.get(sig_key)

    assert token_cookie
    assert signature_cookie

    raw_token_cookie, raw_signature_cookie = [
        value.decode(response.headers.encoding)
        for key, value in response.headers.raw
        if key.lower() == b"set-cookie"
    ]

    assert raw_token_cookie
    assert raw_signature_cookie

    assert token_cookie.value.count(".") == 1
    assert signature_cookie.value.count(".") == 0
    assert "HttpOnly" not in raw_token_cookie
    assert "HttpOnly" in raw_signature_cookie

    access_token = ".".join([token_cookie.value, signature_cookie.value])

    payload_cookie = jwt.decode(
        access_token,
        sanicjwt.config.secret(),
        algorithms=sanicjwt.config.algorithm(),
    )

    assert isinstance(payload_cookie, dict)
    assert sanicjwt.config.user_id() in payload_cookie

    _, response = sanic_app.test_client.get(
        "/auth/verify",
        cookies={
            sanicjwt.config.cookie_access_token_name(): token_cookie.value,
            sanicjwt.config.cookie_split_signature_name(): signature_cookie.value,
        },
    )

    assert response.status == 200
    assert response.json.get("valid") == True


def test_with_cookie_normal(app):
    sanic_app, sanicjwt = app
    sanicjwt.config.cookie_set.update(True)

    _, response = sanic_app.test_client.post(
        "/auth",
        json={"username": "user1", "password": "abcxyz"},
        raw_cookies=True,
    )

    raw_token_cookie = [
        value.decode(response.headers.encoding)
        for key, value in response.headers.raw
        if key.lower() == b"set-cookie"
    ][0]

    assert raw_token_cookie
    assert "httponly" in raw_token_cookie.lower()
    assert "expired" not in raw_token_cookie.lower()
    assert "secure" not in raw_token_cookie.lower()
    assert "max-age" not in raw_token_cookie.lower()


def test_with_cookie_config(app):
    sanic_app, sanicjwt = app
    sanicjwt.config.cookie_set.update(True)
    sanicjwt.config.cookie_httponly.update(False)
    sanicjwt.config.cookie_expires.update(datetime(2100, 1, 1))
    sanicjwt.config.cookie_secure.update(True)
    sanicjwt.config.cookie_max_age.update(10)

    _, response = sanic_app.test_client.post(
        "/auth",
        json={"username": "user1", "password": "abcxyz"},
        raw_cookies=True,
    )

    raw_token_cookie = [
        value.decode(response.headers.encoding)
        for key, value in response.headers.raw
        if key.lower() == b"set-cookie"
    ][0]
    assert raw_token_cookie
    assert "httponly" not in raw_token_cookie.lower()
    assert "expires=fri, 01-jan-2100 00:00:00 gmt" in raw_token_cookie.lower()
    assert "secure" in raw_token_cookie.lower()
    assert "max-age=10" in raw_token_cookie.lower()
