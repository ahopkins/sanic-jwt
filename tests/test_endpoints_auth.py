import jwt
import pytest


@pytest.fixture
def access_token(app):
    _, response = app.test_client.post('/auth', json={
        'username': 'user1',
        'password': 'abcxyz'
    })
    return response.json.get(app.config.SANIC_JWT_ACCESS_TOKEN_NAME, None)


@pytest.fixture
def payload(app, access_token):
    return jwt.decode(access_token, app.config.SANIC_JWT_SECRET)


class TestEndpointsAuth(object):

    def dispatch(self, path, method, app, access_token):
        header_token = '{} {}'.format(app.config.SANIC_JWT_AUTHORIZATION_HEADER_PREFIX, access_token)
        method = getattr(app.test_client, method)
        request, response = method(
            path,
            headers={
                app.config.SANIC_JWT_AUTHORIZATION_HEADER: header_token
            })
        return request, response

    def get(self, path, app, access_token):
        return self.dispatch(path, 'get', app, access_token)

    def test_verify_token(self, app, access_token):
        _, response = self.get('/auth/verify', app, access_token)

        assert response.status == 200
        assert response.json.get('valid') is True

    def test_protected(self, app, access_token):
        _, response = self.get('/protected', app, access_token)

        assert response.status == 200
        assert response.json.get('protected') is True
