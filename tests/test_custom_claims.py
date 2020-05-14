import pytest
from sanic import Sanic

import jwt
from sanic_jwt import Claim, exceptions, Initialize


def test_claim_initialized_properly(app_with_custom_claims):
    sanic_app, sanic_jwt = app_with_custom_claims

    assert len(sanic_app.auth._custom_claims) == 1

    claim = list(sanic_app.auth._custom_claims)[0]
    assert isinstance(claim, Claim)


def test_custom_claims_payload(app_with_custom_claims):
    sanic_app, sanic_jwt = app_with_custom_claims
    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )
    access_token = response.json.get(
        sanic_jwt.config.access_token_name(), None
    )
    payload = jwt.decode(
        access_token,
        sanic_jwt.config.secret(),
        algorithms=sanic_jwt.config.algorithm(),
    )

    assert isinstance(payload, dict)
    assert "username" in payload
    assert payload.get("username") == "user1"


def test_custom_claims(app_with_custom_claims):
    sanic_app, sanic_jwt = app_with_custom_claims
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
    assert "Invalid claim: username." in response.json.get("reasons")

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


def test_custom_claims_bad(authenticate):
    class MissingVerifyClaim(Claim):
        key = "username"

        def setup(self, payload, user):
            return user.username

    class MissingSetupClaim(Claim):
        key = "username"

        def verify(self, payload, value):
            return True

    class MissingKeyClaim(Claim):
        def setup(self, payload, user):
            return user.username

        def verify(self, payload, value):
            return True

    class BogusClaim:
        pass

    with pytest.raises(exceptions.InvalidCustomClaim):
        sanic_app = Sanic("sanic-jwt-test")
        Initialize(
            sanic_app,
            authenticate=authenticate,
            custom_claims=[MissingVerifyClaim],
        )
    with pytest.raises(exceptions.InvalidCustomClaim):
        sanic_app = Sanic("sanic-jwt-test")
        Initialize(
            sanic_app,
            authenticate=authenticate,
            custom_claims=[MissingSetupClaim],
        )
    with pytest.raises(exceptions.InvalidCustomClaim):
        sanic_app = Sanic("sanic-jwt-test")
        Initialize(
            sanic_app,
            authenticate=authenticate,
            custom_claims=[MissingKeyClaim],
        )
    with pytest.raises(exceptions.InvalidCustomClaim):
        sanic_app = Sanic("sanic-jwt-test")
        Initialize(
            sanic_app, authenticate=authenticate, custom_claims=[BogusClaim]
        )


def test_custom_claim_non_boolean_return():
    class CustomClaim(Claim):
        key = "foo"

        def setup(self, **kwargs):
            return "bar"

        def verify(self, value):
            return 123

    myclaim = CustomClaim()
    payload = {"foo": "bar"}

    with pytest.raises(exceptions.InvalidCustomClaim):
        myclaim._verify(payload)
