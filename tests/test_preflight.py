def test_preflight_authenticate(app):
    sanic_app, _ = app
    _, response = sanic_app.test_client.options("/auth")

    assert response.status == 204
    assert not response.body


def test_preflight_retrieve_user(app):
    sanic_app, _ = app
    _, response = sanic_app.test_client.options("/auth/me")

    assert response.status == 204
    assert not response.body


def test_preflight_verify(app):
    sanic_app, _ = app
    _, response = sanic_app.test_client.options("/auth/verify")

    assert response.status == 204
    assert not response.body


def test_preflight_refresh(app_with_refresh_token):
    sanic_app, _ = app_with_refresh_token
    _, response = sanic_app.test_client.options("/auth/refresh")

    assert response.status == 204
    assert not response.body


def test_preflight_refresh_no_refresh_endpoint(app):
    sanic_app, _ = app
    _, response = sanic_app.test_client.options("/auth/refresh")

    assert response.status == 404
