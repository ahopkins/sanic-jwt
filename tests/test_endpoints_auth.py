import jwt
import pytest


@pytest.fixture
def access_token(app):
    sanic_app, sanic_jwt = app
    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )
    return response.json.get(sanic_jwt.config.access_token_name(), None)


@pytest.fixture
def payload(app, access_token):
    _, sanic_jwt = app
    return jwt.decode(access_token, sanic_jwt.config.secret())


class TestEndpointsAuth(object):

    def dispatch(self, path, method, app, access_token):
        sanic_app, sanic_jwt = app
        header_token = "{} {}".format(
            sanic_jwt.config.authorization_header_prefix(), access_token
        )
        method = getattr(sanic_app.test_client, method)
        request, response = method(
            path,
            headers={sanic_jwt.config.authorization_header(): header_token},
        )
        return request, response

    def get(self, path, app, access_token):
        return self.dispatch(path, "get", app, access_token)

    def test_verify_token(self, app, access_token):
        _, response = self.get("/auth/verify", app, access_token)

        assert response.status == 200
        assert response.json.get("valid") is True

    def test_protected(self, app, access_token):
        _, response = self.get("/protected", app, access_token)

        assert response.status == 200
        assert response.json.get("protected") is True
