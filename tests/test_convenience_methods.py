import pytest


@pytest.mark.asyncio
async def test_is_authenticated_on_non_authenticated_request(app):
    sanic_app, _ = app
    request, _ = await sanic_app.asgi_client.get("/protected")

    is_authenticated = await sanic_app.ctx.auth.is_authenticated(request)

    assert isinstance(is_authenticated, bool)
    assert is_authenticated is False


@pytest.mark.asyncio
async def test_is_authenticated_on_properly_authenticated_request(app):
    sanic_app, sanic_jwt = app
    _, response = await sanic_app.asgi_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    access_token = response.json.get(
        sanic_jwt.config.access_token_name(), None
    )

    request, _ = await sanic_app.asgi_client.get(
        "/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    is_authenticated = await sanic_app.ctx.auth.is_authenticated(request)

    assert isinstance(is_authenticated, bool)
    assert is_authenticated is True


@pytest.mark.asyncio
async def test_extract_user_id(app):
    sanic_app, sanic_jwt = app
    _, response = await sanic_app.asgi_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    access_token = response.json.get(
        sanic_jwt.config.access_token_name(), None
    )

    request, _ = await sanic_app.asgi_client.get(
        "/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    user_id = await sanic_app.ctx.auth.extract_user_id(request)

    assert user_id == 1
