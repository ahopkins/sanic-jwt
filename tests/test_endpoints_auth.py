import jwt

from . import app

_, response = app.test_client.post('/auth', json={
    'username': 'user1',
    'password': 'abcxyz'
})

access_token = response.json.get(app.config.SANIC_JWT_ACCESS_TOKEN_NAME, None)
payload = jwt.decode(access_token, app.config.SANIC_JWT_SECRET)


class TestEndpointsAuth(object):
    def dispatch(self, path, method):
        header_token = '{} {}'.format(app.config.SANIC_JWT_AUTHORIZATION_HEADER_PREFIX, access_token)
        method = getattr(app.test_client, method)
        request, response = method('/auth/verify', headers={
            app.config.SANIC_JWT_AUTHORIZATION_HEADER: header_token
        })
        return request, response

    def get(self, path):
        return self.dispatch(path, 'get')

    def test_verify_token(self):
        _, response = self.get('/auth/verify')

        assert response.status == 200
        assert response.json.get('valid') is True
