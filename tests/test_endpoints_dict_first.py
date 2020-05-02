from sanic import Sanic

import pytest
from sanic_jwt import exceptions, Initialize


class MyCustomDict(dict):
    async def to_dict(self):
        raise Exception("i am not supposed to be called")


@pytest.yield_fixture
def app_with_dict_test():

    the_user = MyCustomDict(user_id=1)

    async def retrieve_user(request, payload, *args, **kwargs):
        return the_user

    async def authenticate(request, *args, **kwargs):
        username = request.json.get("username", None)
        password = request.json.get("password", None)

        if not username or not password:
            raise exceptions.AuthenticationFailed(
                "Missing username or password."
            )

        user = the_user

        return user

    sanic_app = Sanic("sanic-jwt-test")
    sanicjwt = Initialize(
        sanic_app, authenticate=authenticate, retrieve_user=retrieve_user
    )

    yield (sanic_app, sanicjwt)


class TestEndpointsAsync(object):
    @pytest.yield_fixture
    def authenticated_response(self, app_with_dict_test):
        app, sanicjwt = app_with_dict_test
        _, response = app.test_client.post(
            "/auth", json={"username": "foo", "password": "bar"}
        )
        assert response.status == 200
        yield response

    def test_me_endpoint(self, app_with_dict_test, authenticated_response):
        app, sanicjwt = app_with_dict_test
        access_token = authenticated_response.json.get(
            sanicjwt.config.access_token_name(), None
        )

        _, response = app.test_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("me").get("user_id") == 1
