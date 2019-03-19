import pytest
from sanic import Sanic
from sanic.response import json

from sanic_jwt import Authentication, exceptions, Initialize


class WrongAuthentication(Authentication):
    async def build_payload(self, user, *args, **kwargs):
        return {"not_user_id": 1}


class AnotherWrongAuthentication(Authentication):
    async def build_payload(self, user, *args, **kwargs):
        return list(range(5))


class AuthenticationWithNoMethod(Authentication):

    authenticate = "foobar"


class AuthenticationInClassBody(Authentication):
    async def authenticate(self, request, *args, **kwargs):
        return {"user_id": 1}


async def authenticate(request, *args, **kwargs):
    return {"user_id": 1}


def test_authentication_subclass_without_authenticate_parameter():

    app = Sanic()

    with pytest.raises(exceptions.AuthenticateNotImplemented):

        Initialize(app, authentication_class=WrongAuthentication)


def test_authentication_subclass_with_autenticate_not_as_method():

    app = Sanic()

    with pytest.raises(exceptions.AuthenticateNotImplemented):

        Initialize(app, authentication_class=AuthenticationWithNoMethod)


def test_authentication_subbclass_with_method_in_class():

    app = Sanic()

    sanicjwt = Initialize(app, authentication_class=AuthenticationInClassBody)

    _, response = app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    assert response.status == 200
    assert sanicjwt.config.access_token_name() in response.json


def test_payload_without_correct_key():

    app = Sanic()

    Initialize(app, authenticate=authenticate, authentication_class=WrongAuthentication)

    _, response = app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    assert response.status == 500
    assert response.json.get("exception") == "InvalidPayload"


def test_payload_not_a_dict():

    app = Sanic()

    Initialize(
        app, authenticate=authenticate, authentication_class=AnotherWrongAuthentication
    )

    _, response = app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    assert response.status == 500
    assert response.json.get("exception") == "InvalidPayload"


def test_wrong_header(app):
    sanic_app, sanic_jwt = app
    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    access_token = response.json.get(sanic_jwt.config.access_token_name(), None)

    assert response.status == 200
    assert access_token is not None

    _, response = sanic_app.test_client.get(
        "/protected", headers={"Authorization": "Foobar {}".format(access_token)}
    )

    assert response.status == 401
    assert response.json.get("exception") == "Unauthorized"
    assert "Authorization header is invalid." in response.json.get("reasons")


# assert "Auth required." in response.json.get('reasons')


def test_tricky_debug_option_true(app):
    sanic_app, sanic_jwt = app

    @sanic_app.route("/another_protected")
    @sanic_jwt.protected(debug=lambda: True)
    def another_protected(request):
        return json({"protected": True, "is_debug": request.app.auth.config.debug()})

    # @sanic_app.exception(Exception)
    # def in_case_of_exception(request, exception):
    #     exc_name = exception.args[0].__class__.__name__
    #     status_code = exception.args[0].status_code
    #     return json({"exception": exc_name}, status=status_code)

    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    access_token = response.json.get(sanic_jwt.config.access_token_name(), None)

    assert response.status == 200
    assert access_token is not None

    _, response = sanic_app.test_client.get(
        "/protected", headers={"Authorization": "Bearer {}".format(access_token)}
    )

    assert response.status == 200

    _, response = sanic_app.test_client.get("/another_protected")

    assert response.json.get("exception") == "Unauthorized"
    assert response.status == 400
    assert "Authorization header not present." in response.json.get("reasons")

    _, response = sanic_app.test_client.get(
        "/another_protected",
        headers={"Authorization": "Foobar {}".format(access_token)},
    )

    assert response.json.get("exception") == "Unauthorized"
    assert response.status == 400
    assert "Authorization header is invalid." in response.json.get("reasons")


def test_tricky_debug_option_false(app):
    sanic_app, sanic_jwt = app

    @sanic_app.route("/another_protected")
    @sanic_jwt.protected(debug=lambda: False)
    def another_protected(request):
        return json({"protected": True, "is_debug": request.app.auth.config.debug()})

    # @sanic_app.exception(Exception)
    # def in_case_of_exception(request, exception):
    #     exc_name = exception.args[0].__class__.__name__
    #     status_code = exception.args[0].status_code
    #     return json({"exception": exc_name}, status=status_code)

    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    access_token = response.json.get(sanic_jwt.config.access_token_name(), None)

    assert response.status == 200
    assert access_token is not None

    _, response = sanic_app.test_client.get(
        "/protected", headers={"Authorization": "Bearer {}".format(access_token)}
    )

    assert response.status == 200

    _, response = sanic_app.test_client.get("/another_protected")

    assert response.json.get("exception") == "Unauthorized"
    assert response.status == 401
    assert "Authorization header not present." in response.json.get("reasons")

    _, response = sanic_app.test_client.get(
        "/another_protected",
        headers={"Authorization": "Foobar {}".format(access_token)},
    )

    assert response.json.get("exception") == "Unauthorized"
    assert response.status == 401
    assert "Authorization header is invalid." in response.json.get("reasons")
