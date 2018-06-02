import jwt


def test_unprotected(app):
    sanic_app, _ = app
    _, response = sanic_app.test_client.get("/")
    assert response.status == 200


def test_protected(app):
    sanic_app, _ = app
    _, response = sanic_app.test_client.get("/protected")
    assert response.status == 401


def test_options(app):
    sanic_app, _ = app
    _, response = sanic_app.test_client.options("/options")

    assert response.body == b""
    assert response.status == 204


def test_auth_invalid_method(app):
    sanic_app, _ = app
    _, response = sanic_app.test_client.get("/auth")
    assert response.status == 405


def test_auth_proper_credentials(app):
    sanic_app, sanic_jwt = app
    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    access_token = response.json.get(
        sanic_jwt.config.access_token_name(), None
    )
    payload = jwt.decode(access_token, sanic_jwt.config.secret())

    assert response.status == 200
    assert access_token is not None
    assert isinstance(payload, dict)
    assert sanic_jwt.config.user_id() in payload
    assert "exp" in payload

    _, response = sanic_app.test_client.get(
        "/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )
    assert response.status == 200


def test_auth_verify_missing_token(app):
    sanic_app, _ = app
    _, response = sanic_app.test_client.get("/auth/verify")
    assert response.status == 400


def test_auth_refresh_not_found(app):
    sanic_app, _ = app
    _, response = sanic_app.test_client.post("/auth/refresh")
    assert response.status == 404  # since refresh_token_enabled is False


def test_auth_refresh_not_enabled(app_with_refresh_token):
    sanic_app, _ = app_with_refresh_token
    _, response = sanic_app.test_client.post("/auth/refresh")
    assert response.status == 400
