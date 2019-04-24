import binascii
import os
import uuid

from datetime import datetime, timedelta
from freezegun import freeze_time
from sanic import Sanic
from sanic.response import json

import pytest
from sanic_jwt import Initialize
from sanic_jwt import exceptions
from sanic_jwt.decorators import protected


def generate_refresh_token(*args, **kwargs):
    return str(uuid.uuid4())


@pytest.yield_fixture
def app_with_sync_methods(users):

    cache = {}

    def authenticate(request, *args, **kwargs):
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

    def store_refresh_token(user_id, refresh_token, *args, **kwargs):
        key = "refresh_token_{user_id}".format(user_id=user_id)
        cache[key] = refresh_token

    def retrieve_refresh_token(user_id, *args, **kwargs):
        key = "refresh_token_{user_id}".format(user_id=user_id)
        return cache.get(key, None)

    def retrieve_user(request, payload, *args, **kwargs):
        if payload:
            user_id = payload.get("user_id", None)
            if user_id is not None:
                for u in users:
                    if u.user_id == user_id:
                        return u

        else:
            return None

    sanic_app = Sanic()
    sanicjwt = Initialize(
        sanic_app,
        authenticate=authenticate,
        store_refresh_token=store_refresh_token,
        retrieve_refresh_token=retrieve_refresh_token,
        retrieve_user=retrieve_user,
        generate_refresh_token=generate_refresh_token,
    )

    sanic_app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED = True
    sanic_app.config.SANIC_JWT_SECRET = str(
        binascii.hexlify(os.urandom(32)), "utf-8"
    )

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    yield (sanic_app, sanicjwt)


class TestEndpointsSync(object):
    @pytest.yield_fixture
    def authenticated_response(self, app_with_sync_methods):
        sanic_app, _ = app_with_sync_methods
        _, response = sanic_app.test_client.post(
            "/auth", json={"username": "user1", "password": "abcxyz"}
        )
        assert response.status == 200
        yield response

    def test_root_endpoint(self, app_with_sync_methods):
        sanic_app, sanicjwt = app_with_sync_methods
        _, response = sanic_app.test_client.get("/")
        assert response.status == 200
        assert response.json.get("hello") == "world"

    def test_protected_endpoint(
        self, app_with_sync_methods, authenticated_response
    ):
        sanic_app, sanicjwt = app_with_sync_methods
        access_token = authenticated_response.json.get(
            sanicjwt.config.access_token_name(), None
        )

        _, response = sanic_app.test_client.get(
            "/protected",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True

    def test_me_endpoint(self, app_with_sync_methods, authenticated_response):
        sanic_app, sanicjwt = app_with_sync_methods
        access_token = authenticated_response.json.get(
            sanicjwt.config.access_token_name(), None
        )

        _, response = sanic_app.test_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200

    def test_verify_endpoint_with_error(
        self, app_with_sync_methods, authenticated_response
    ):
        sanic_app, sanicjwt = app_with_sync_methods
        access_token = authenticated_response.json.get(
            sanicjwt.config.access_token_name(), None
        )

        with freeze_time(datetime.utcnow() + timedelta(seconds=(60 * 5 * 60))):
            _, response = sanic_app.test_client.get(
                "/auth/verify",
                headers={"Authorization": "Bearer {}".format(access_token)},
            )

            assert response.status == 401
            assert response.json.get("exception") == "InvalidToken"
            assert "Signature has expired." in response.json.get("reasons")

    def test_refresh_token_sync(
        self, app_with_sync_methods, authenticated_response
    ):
        sanic_app, sanicjwt = app_with_sync_methods
        access_token = authenticated_response.json.get(
            sanicjwt.config.access_token_name(), None
        )
        refresh_token = authenticated_response.json.get(
            sanicjwt.config.refresh_token_name(), None
        )

        _, response = sanic_app.test_client.post(
            "/auth/refresh",
            headers={"Authorization": "Bearer {}".format(access_token)},
            json={sanicjwt.config.refresh_token_name(): refresh_token},
        )

        new_access_token = response.json.get(
            sanicjwt.config.access_token_name(), None
        )

        assert response.status == 200
        assert new_access_token is not None
        assert (
            response.json.get(sanicjwt.config.refresh_token_name(), None)
            is None
        )  # there is no new refresh token
        assert sanicjwt.config.refresh_token_name() not in response.json
