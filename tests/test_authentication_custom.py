import pytest
from sanic import Sanic

from sanic_jwt import Authentication, Initialize


@pytest.yield_fixture
def app1():
    class MyAuthentication(Authentication):
        async def store_refresh_token(self, *args, **kwargs):
            return

        async def retrieve_refresh_token(self, *args, **kwargs):
            return

        async def authenticate(self, *args, **kwargs):
            return

        async def retrieve_user(self, *args, **kwargs):
            return

        def extract_payload(self, request, verify=True, *args, **kwargs):
            return

    app = Sanic()
    Initialize(
        app,
        authentication_class=MyAuthentication,
        refresh_token_enabled=True)

    yield app


@pytest.yield_fixture
def app2():
    class MyAuthentication(Authentication):
        async def store_refresh_token(self, *args, **kwargs):
            return

        async def retrieve_refresh_token(self, *args, **kwargs):
            return {}

        async def authenticate(self, *args, **kwargs):
            return "foobar"

        async def retrieve_user(self, *args, **kwargs):
            return {}

        def extract_payload(self, request, verify=True, *args, **kwargs):
            return {}

    app = Sanic()
    Initialize(
        app,
        authentication_class=MyAuthentication,
        refresh_token_enabled=True)

    yield app


def test_auth_invalid_retrieve_user(app1):
    _, response = app1.test_client.post("/auth", json={"not": "important"})

    assert response.status == 500
    assert response.json.get("exception") == "InvalidRetrieveUserObject"


def test_auth_invalid_something(app2):
    _, response = app2.test_client.post("/auth", json={"not": "important"})

    assert response.status == 500
    assert response.json.get("exception") == "InvalidRetrieveUserObject"


def test_me_with_none(app1):

    _, response = app1.test_client.get("/auth/me")

    assert response.status == 200
    assert response.json.get("me") is None


def test_me_without_authorization_header(app2):

    _, response = app2.test_client.get("/auth/me")

    assert response.status == 200
    assert response.json.get("me") is None


def test_verify_no_auth_header(app1):
    _, response = app1.test_client.get("/auth/verify")

    assert response.status == 400
    assert response.json.get("exception") == "MissingAuthorizationHeader"


def test_refresh_no_valid_object(app1):
    _, response = app1.test_client.post("/auth/refresh", json={"not": "important"})

    assert response.status == 500
    assert response.json.get("exception") == "InvalidRetrieveUserObject"


def test_refresh_no_valid_dict(app2):
    _, response = app2.test_client.post("/auth/refresh", json={"not": "important"})

    assert response.status == 400
    assert response.json.get("exception") == "MissingAuthorizationHeader"
