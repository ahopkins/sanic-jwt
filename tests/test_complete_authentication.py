import jwt
import pytest
from sanic import Sanic
from sanic.response import json
from datetime import datetime, timedelta
from freezegun import freeze_time
from sanic_jwt import Authentication, Initialize, exceptions, protected


@pytest.yield_fixture
def cache():
    yield {}


@pytest.yield_fixture
def my_authentication_class(users, cache):

    class MyAuthentication(Authentication):

        async def authenticate(self, request, *args, **kwargs):
            username = request.json.get("username", None)
            password = request.json.get("password", None)

            if not username or not password:
                raise exceptions.AuthenticationFailed(
                    "Missing username or password."
                )

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

        async def store_refresh_token(
            self, user_id, refresh_token, *args, **kwargs
        ):
            key = "refresh_token_{user_id}".format(user_id=user_id)
            cache[key] = refresh_token

        async def retrieve_refresh_token(self, user_id, *args, **kwargs):
            key = "refresh_token_{user_id}".format(user_id=user_id)
            token = cache.get(key, None)
            return token

        async def retrieve_user(self, request, payload, *args, **kwargs):
            if payload:
                user_id = payload.get("user_id", None)
                if user_id is not None:
                    for u in users:
                        if u.user_id == user_id:
                            return u

            else:
                return None

        async def extend_payload(self, payload, user=None, *args, **kwargs):
            payload.update({"foo": "bar"})
            return payload

    yield MyAuthentication


@pytest.yield_fixture
def sanic_app(users, my_authentication_class, cache):
    sanic_app = Sanic()

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    yield sanic_app


@pytest.yield_fixture
def app_full_auth_cls(sanic_app, my_authentication_class):

    sanicjwt = Initialize(
        sanic_app,
        authentication_class=my_authentication_class,
        refresh_token_enabled=True,
    )

    yield (sanic_app, sanicjwt)


@pytest.yield_fixture
def app_full_bytes_refresh_token(
    users, sanic_app, my_authentication_class, cache
):

    class MyAuthentication(my_authentication_class):

        async def retrieve_refresh_token(self, user_id, *args, **kwargs):
            key = "refresh_token_{user_id}".format(user_id=user_id)
            token = cache.get(key, None).encode("utf-8")
            print(token, type(token))
            return token

    sanicjwt = Initialize(
        sanic_app,
        authentication_class=MyAuthentication,
        refresh_token_enabled=True,
    )

    yield (sanic_app, sanicjwt)


def test_authentication_all_methods(app_full_auth_cls):

    app, sanicjwt = app_full_auth_cls

    _, response = app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    assert response.status == 200
    assert sanicjwt.config.access_token_name() in response.json
    assert sanicjwt.config.refresh_token_name() in response.json

    access_token = response.json.get(sanicjwt.config.access_token_name(), None)
    refresh_token = response.json.get(
        sanicjwt.config.refresh_token_name(), None
    )

    assert access_token is not None
    assert refresh_token is not None

    payload = jwt.decode(access_token, sanicjwt.config.secret())

    assert "foo" in payload
    assert payload.get("foo") == "bar"

    _, response = app.test_client.get(
        "/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 200
    assert response.json.get("protected") is True

    _, response = app.test_client.get(
        "/auth/verify",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 200

    _, response = app.test_client.get(
        "/auth/me", headers={"Authorization": "Bearer {}".format(access_token)}
    )

    assert response.status == 200
    assert "me" in response.json

    _, response = app.test_client.post(
        "/auth/refresh",
        headers={"Authorization": "Bearer {}".format(access_token)},
        json={sanicjwt.config.refresh_token_name(): refresh_token},
    )

    new_access_token = response.json.get(
        sanicjwt.config.access_token_name(), None
    )

    assert response.status == 200
    assert new_access_token is not None
    assert response.json.get(
        sanicjwt.config.refresh_token_name(), None
    ) is None  # there is no new refresh token
    assert sanicjwt.config.refresh_token_name() not in response.json


def test_refresh_token_with_expired_access_token(app_full_auth_cls):

    app, sanicjwt = app_full_auth_cls

    _, response = app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    assert response.status == 200
    assert sanicjwt.config.access_token_name() in response.json
    assert sanicjwt.config.refresh_token_name() in response.json

    access_token = response.json.get(sanicjwt.config.access_token_name(), None)
    refresh_token = response.json.get(
        sanicjwt.config.refresh_token_name(), None
    )

    assert access_token is not None
    assert refresh_token is not None

    with freeze_time(datetime.utcnow() + timedelta(seconds=(60 * 5 * 60))):
        _, response = app.test_client.post(
            "/auth/refresh",
            headers={"Authorization": "Bearer {}".format(access_token)},
            json={sanicjwt.config.refresh_token_name(): refresh_token},
        )

        new_access_token = response.json.get(
            sanicjwt.config.access_token_name(), None
        )

        assert response.status == 200
        assert new_access_token is not None
        assert response.json.get(
            sanicjwt.config.refresh_token_name(), None
        ) is None  # there is no new refresh token
        assert sanicjwt.config.refresh_token_name() not in response.json


def test_authentication_cross_tokens(app_full_auth_cls):

    app, sanicjwt = app_full_auth_cls

    _, response = app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    assert response.status == 200
    assert sanicjwt.config.access_token_name() in response.json
    assert sanicjwt.config.refresh_token_name() in response.json

    access_token_u1 = response.json.get(
        sanicjwt.config.access_token_name(), None
    )

    _, response = app.test_client.post(
        "/auth", json={"username": "user2", "password": "abcxyz"}
    )

    assert response.status == 200
    assert sanicjwt.config.access_token_name() in response.json
    assert sanicjwt.config.refresh_token_name() in response.json

    refresh_token_u2 = response.json.get(
        sanicjwt.config.refresh_token_name(), None
    )

    _, response = app.test_client.post(
        "/auth/refresh",
        headers={"Authorization": "Bearer {}".format(access_token_u1)},
        json={sanicjwt.config.refresh_token_name(): refresh_token_u2},
    )

    assert response.status == 401
    assert response.json.get("exception") == "AuthenticationFailed"
    assert "Authentication failed." in response.json.get("reasons")


def test_authentication_with_bytes_refresh_token(app_full_bytes_refresh_token):

    app, sanicjwt = app_full_bytes_refresh_token

    _, response = app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    assert response.status == 200
    assert sanicjwt.config.access_token_name() in response.json
    assert sanicjwt.config.refresh_token_name() in response.json

    access_token = response.json.get(sanicjwt.config.access_token_name(), None)
    refresh_token = response.json.get(
        sanicjwt.config.refresh_token_name(), None
    )

    assert access_token is not None
    assert refresh_token is not None

    payload = jwt.decode(access_token, sanicjwt.config.secret())

    assert "foo" in payload
    assert payload.get("foo") == "bar"

    _, response = app.test_client.get(
        "/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 200
    assert response.json.get("protected") is True

    _, response = app.test_client.get(
        "/auth/verify",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 200

    _, response = app.test_client.get(
        "/auth/me", headers={"Authorization": "Bearer {}".format(access_token)}
    )

    assert response.status == 200
    assert "me" in response.json

    _, response = app.test_client.post(
        "/auth/refresh",
        headers={"Authorization": "Bearer {}".format(access_token)},
        json={sanicjwt.config.refresh_token_name(): refresh_token},
    )

    new_access_token = response.json.get(
        sanicjwt.config.access_token_name(), None
    )

    assert response.status == 200
    assert new_access_token is not None
    assert response.json.get(
        sanicjwt.config.refresh_token_name(), None
    ) is None  # there is no new refresh token
    assert sanicjwt.config.refresh_token_name() not in response.json
