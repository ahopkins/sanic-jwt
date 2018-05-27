def test_is_authenticated_on_non_authenticated_request(app):
    sanic_app, _ = app
    request, _ = sanic_app.test_client.get("/protected")

    is_authenticated = sanic_app.auth.is_authenticated(request)

    assert isinstance(is_authenticated, bool)
    assert is_authenticated is False


def test_is_authenticated_on_properly_authenticated_request(app):
    sanic_app, sanic_jwt = app
    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    access_token = response.json.get(
        sanic_jwt.config.access_token_name(), None
    )

    request, _ = sanic_app.test_client.get(
        "/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    is_authenticated = sanic_app.auth.is_authenticated(request)

    assert isinstance(is_authenticated, bool)
    assert is_authenticated is True


def test_extract_user_id(app):
    sanic_app, sanic_jwt = app
    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    access_token = response.json.get(
        sanic_jwt.config.access_token_name(), None
    )

    request, _ = sanic_app.test_client.get(
        "/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    user_id = sanic_app.auth.extract_user_id(request)

    assert user_id == 1
