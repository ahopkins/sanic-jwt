from sanic import response, Sanic
from sanic.response import json

from sanic_jwt import BaseEndpoint, initialize


class MagicLoginHandler(BaseEndpoint):
    async def options(self, request):
        return response.text("", status=204)

    async def post(self, request):
        # create a magic login token and email it to the user

        response = {"magic-token": "123456789"}
        return json(response)


app = Sanic("sanic-jwt-test")
initialize(
    app,
    authenticate=lambda: True,
    class_views=[
        (
            "/magic-login",
            MagicLoginHandler,
        )  # The path will be relative to the url prefix
        # (which defaults to /auth)
    ],
)


class TestEndpointsExtra(object):
    def dispatch(self, path, method):
        method = getattr(app.test_client, method)
        request, response = method(path)
        return request, response

    def get(self, path):
        return self.dispatch(path, "get")

    def post(self, path):
        return self.dispatch(path, "post")

    def options(self, path):
        return self.dispatch(path, "options")

    def test_verify_token(self):
        _, response = self.options("/auth/magic-login")
        assert response.status == 204

        _, response = self.post("/auth/magic-login")

        assert response.status == 200
        assert response.json.get("magic-token") == "123456789"
