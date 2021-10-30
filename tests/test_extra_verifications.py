from sanic import Sanic
from sanic.response import json

from sanic_jwt import Initialize, protected


def test_extra_verification_passing(app_with_extra_verification):
    sanic_app, sanic_jwt = app_with_extra_verification
    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    access_token = response.json.get(
        sanic_jwt.config.access_token_name(), None
    )
    _, response = sanic_app.test_client.get(
        "/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 401
    assert "Verifications were not met." in response.json.get("reasons")

    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user2", "password": "abcxyz"}
    )

    access_token = response.json.get(
        sanic_jwt.config.access_token_name(), None
    )
    _, response = sanic_app.test_client.get(
        "/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 200


def test_extra_verification_non_boolean_return(authenticate):
    def bad_return(payload, request):
        return 123

    extra_verifications = [bad_return]

    sanic_app = Sanic("sanic-jwt-test")
    sanic_jwt = Initialize(
        sanic_app,
        debug=True,
        authenticate=authenticate,
        extra_verifications=extra_verifications,
    )

    @sanic_app.route("/protected", error_format="json")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    access_token = response.json.get(
        sanic_jwt.config.access_token_name(), None
    )

    _, response = sanic_app.test_client.get(
        "/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 500
    assert "Verifications must be a callable object "


def test_extra_verification_non_callable(authenticate):

    extra_verifications = [123]

    sanic_app = Sanic("sanic-jwt-test")
    sanic_jwt = Initialize(
        sanic_app,
        debug=True,
        authenticate=authenticate,
        extra_verifications=extra_verifications,
    )

    @sanic_app.route("/protected", error_format="json")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    access_token = response.json.get(
        sanic_jwt.config.access_token_name(), None
    )

    _, response = sanic_app.test_client.get(
        "/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 500
    assert "Verifications must be a callable object "
    "returning a boolean value." in response.json.get("reasons")
