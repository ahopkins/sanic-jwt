from datetime import datetime, timedelta

import jwt
from freezegun import freeze_time


def test_unexpired(app):
    sanic_app, sanic_jwt = app
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
    exp = payload.get("exp", None)

    assert "exp" in payload

    exp = datetime.utcfromtimestamp(exp)

    assert isinstance(exp, datetime)
    assert datetime.utcnow() < exp

    _, response = sanic_app.test_client.get(
        "/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 200


def test_expired(app):
    sanic_app, sanic_jwt = app
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
    exp = payload.get("exp", None)

    assert "exp" in payload

    exp = datetime.utcfromtimestamp(exp)

    with freeze_time(datetime.utcnow() + timedelta(seconds=(60 * 35))):
        assert isinstance(exp, datetime)
        assert datetime.utcnow() > exp

        _, response = sanic_app.test_client.get(
            "/protected",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 401
        assert response.json.get("description") == "Unauthorized"
        assert "Signature has expired." in response.json.get("message")

        # regression test see
        # https://github.com/ahopkins/sanic-jwt/issues/59#issuecomment-380034269
        _, response = sanic_app.test_client.get(
            "/protected/0/",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 401
        assert response.json.get("description") == "Unauthorized"
        assert "Signature has expired." in response.json.get("message")


def test_exp_configuration(app_with_extended_exp):
    sanic_app, sanic_jwt = app_with_extended_exp
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
        verify=False,
    )
    exp = payload.get("exp", None)
    exp = datetime.utcfromtimestamp(exp)

    with freeze_time(datetime.utcnow() + timedelta(seconds=(60 * 35))):
        assert isinstance(exp, datetime)
        assert datetime.utcnow() < exp

        _, response = sanic_app.test_client.get(
            "/protected",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )
        assert response.status == 200


def test_leeway_configuration(app_with_leeway):
    sanic_app, sanic_jwt = app_with_leeway
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
        verify=False,
    )
    exp = payload.get("exp", None)
    exp = datetime.utcfromtimestamp(exp)

    with freeze_time(datetime.utcnow() + timedelta(seconds=(60 * 35 + 1))):
        _, response = sanic_app.test_client.get(
            "/protected",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )
        assert response.status == 401
        assert response.json.get("description") == "Unauthorized"
        assert "Signature has expired." in response.json.get("message")

    with freeze_time(datetime.utcnow() + timedelta(seconds=(60 * 35 - 1))):
        _, response = sanic_app.test_client.get(
            "/protected",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )
        assert response.status == 200


def test_nbf(app_with_nbf):
    sanic_app, sanic_jwt = app_with_nbf
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
        verify=False,
        leeway=60 * 9,
    )
    exp = payload.get("exp", None)
    exp = datetime.utcfromtimestamp(exp)

    assert "nbf" in payload
    assert isinstance(payload.get("nbf"), int)

    _, response = sanic_app.test_client.get(
        "/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 401
    assert response.json.get("description") == "Unauthorized"
    assert "The token is not yet valid (nbf)." in response.json.get("message")

    with freeze_time(datetime.utcnow() + timedelta(seconds=(60 * 5 - 10))):
        _, response = sanic_app.test_client.get(
            "/protected",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 401
        assert response.json.get("description") == "Unauthorized"
        assert "The token is not yet valid (nbf)." in response.json.get(
            "message"
        )

    with freeze_time(datetime.utcnow() + timedelta(seconds=(60 * 5 + 10))):
        _, response = sanic_app.test_client.get(
            "/protected",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200


def test_iat(app_with_iat):
    sanic_app, sanic_jwt = app_with_iat
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
        verify=False,
    )

    assert "iat" in payload
    assert isinstance(payload.get("iat"), int)

    _, response = sanic_app.test_client.get(
        "/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 200


def test_iss(app_with_iss):
    sanic_app, sanic_jwt = app_with_iss
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
        verify=False,
    )

    assert "iss" in payload
    assert isinstance(payload.get("iss"), str)

    _, response = sanic_app.test_client.get(
        "/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 200
    assert payload.get("iss") == "issuingserver"


def test_aud(app_with_aud):
    sanic_app, sanic_jwt = app_with_aud
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
        verify=False,
        audience=sanic_jwt.config.claim_aud(),
    )

    assert "aud" in payload
    assert isinstance(payload.get("aud"), str)

    _, response = sanic_app.test_client.get(
        "/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 200
    assert payload.get("aud") == "clientserver"
