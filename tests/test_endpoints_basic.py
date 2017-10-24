import jwt

from sanic_jwt import exceptions
from . import app


class TestEndpointsBasic(object):
    def test_unprotected(self):
        _, response = app.test_client.get('/')
        assert response.status == 200

    def test_protected(self):
        _, response = app.test_client.get('/protected')
        assert response.status == 401

    def test_auth_invalid_method(self):
        _, response = app.test_client.get('/auth')
        assert response.status == 405

    def test_auth_proper_credentials(self):
        _, response = app.test_client.post('/auth', json={
            'username': 'user1',
            'password': 'abcxyz'
        })

        access_token = response.json.get(app.config.SANIC_JWT_ACCESS_TOKEN_NAME, None)
        payload = jwt.decode(access_token, app.config.SANIC_JWT_SECRET)

        assert response.status == 200
        assert access_token is not None
        assert isinstance(payload, dict)
        assert app.config.SANIC_JWT_USER_ID in payload
        assert 'exp' in payload

    def test_auth_verify_missing_token(self):
        try:
            _, response = app.test_client.get('/auth/verify')
        except Exception as e:
            assert isinstance(e, exceptions.MissingAuthorizationHeader)

    def test_auth_refresh_not_enabled(self):
        try:
            _, response = app.test_client.get('/auth/refresh')
        except Exception as e:
            assert isinstance(e, exceptions.MissingAuthorizationHeader)
