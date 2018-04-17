import jwt
import pytest
from sanic import Sanic
from sanic.response import json

from sanic_jwt import Authentication, Initialize, exceptions


@pytest.yield_fixture
def app_full_auth_cls(users):

    cache = {}

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
            return cache.get(key, None)

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

    sanic_app = Sanic()
    sanicjwt = Initialize(
        sanic_app,
        authentication_class=MyAuthentication,
        refresh_token_enabled=True,
    )

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @sanicjwt.protected()
    async def protected_request(request):
        return json({"protected": True})

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
