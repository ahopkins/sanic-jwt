import pytest


@pytest.fixture
def access_token(app_with_url_prefix):
    sanic_app, sanic_jwt = app_with_url_prefix
    print(sanic_jwt._get_url_prefix())
    _, response = sanic_app.test_client.post(
        "/somethingelse", json={"username": "user1", "password": "abcxyz"}
    )
    return response.json.get(sanic_jwt.config.access_token_name(), None)


class TestEndpointsAuth:
    def dispatch(self, path, method, app_with_url_prefix, access_token):
        sanic_app, sanic_jwt = app_with_url_prefix
        header_token = "{} {}".format(
            sanic_jwt.config.authorization_header_prefix(), access_token
        )
        method = getattr(sanic_app.test_client, method)
        request, response = method(
            path, headers={sanic_jwt.config.authorization_header(): header_token}
        )
        return request, response

    def get(self, path, app_with_url_prefix, access_token):
        return self.dispatch(path, "get", app_with_url_prefix, access_token)

    def test_verify_token(self, app_with_url_prefix, access_token):
        _, response = self.get(
            "/somethingelse/verify", app_with_url_prefix, access_token
        )

        assert response.status == 200
        assert response.json.get("valid") is True

    def test_protected(self, app_with_url_prefix, access_token):
        _, response = self.get("/protected/", app_with_url_prefix, access_token)

        assert response.status == 200
        assert response.json.get("protected") is True
