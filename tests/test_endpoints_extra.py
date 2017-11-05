from sanic import Sanic, response
from sanic.views import HTTPMethodView
from sanic.response import json
from sanic_jwt import initialize


class MagicLoginHandler(HTTPMethodView):
    async def options(self, request):
        return response.text('', status=204)

    async def post(self, request):
        # create a magic login token and email it to the user

        response = {
            'magic-token': '123456789'
        }
        return json(response)


app = Sanic()
initialize(
    app,
    authenticate=lambda: True,
    class_views=[
        ('/magic-login', MagicLoginHandler)     # The path will be relative to the url prefix (which defaults to /auth)
    ]
)


class TestEndpointsExtra(object):
    def dispatch(self, path, method):
        # header_token = '{} {}'.format(app.config.SANIC_JWT_AUTHORIZATION_HEADER_PREFIX, access_token)
        method = getattr(app.test_client, method)
        request, response = method(path)
        return request, response

    def get(self, path):
        return self.dispatch(path, 'get')

    def post(self, path):
        return self.dispatch(path, 'post')

    def options(self, path):
        return self.dispatch(path, 'options')

    def test_verify_token(self):
        _, response = self.options('/auth/magic-login')
        assert response.status == 204

        _, response = self.post('/auth/magic-login')

        assert response.status == 200
        assert response.json.get('magic-token') == '123456789'
