import jwt


class TestEndpointsBasic(object):
    def test_unprotected(self, app):
        _, response = app.test_client.get('/')
        assert response.status == 200

    def test_protected(self, app):
        _, response = app.test_client.get('/protected')
        assert response.status == 401

    def test_auth_invalid_method(self, app):
        _, response = app.test_client.get('/auth')
        assert response.status == 405

    def test_auth_proper_credentials(self, app):
        _, response = app.test_client.post('/auth', json={
            'username': 'user1',
            'password': 'abcxyz'
        })

        access_token = response.json.get(
            app.config.SANIC_JWT_ACCESS_TOKEN_NAME, None)
        payload = jwt.decode(access_token, app.config.SANIC_JWT_SECRET)

        assert response.status == 200
        assert access_token is not None
        assert isinstance(payload, dict)
        assert app.config.SANIC_JWT_USER_ID in payload
        assert 'exp' in payload

        _, response = app.test_client.get('/protected', headers={
            'Authorization': 'Bearer {}'.format(access_token)
        })
        assert response.status == 200

    def test_auth_verify_missing_token(self, app):
        _, response = app.test_client.get('/auth/verify')
        assert response.status == 400

    def test_auth_refresh_not_enabled(self, app):
        _, response = app.test_client.post('/auth/refresh')
        assert response.status == 400
