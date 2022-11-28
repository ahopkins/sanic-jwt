import pytest
from sanic import Sanic
from sanic.response import json

import sanic_jwt
from sanic_jwt import initialize


class TestEndpointsScoped(object):
    @pytest.fixture
    def app_with_simple_scope(self):
        sanic_app = Sanic("sanic-jwt-test")
        sanicjwt = initialize(sanic_app, authenticate=lambda: True)

        @sanic_app.route("/scoped_empty")
        @sanic_jwt.scoped("something")
        async def scoped(request):
            return json({"scoped": True})

        yield sanic_app, sanicjwt

    def test_scoped_empty(self, app_with_simple_scope):
        sanic_app, _ = app_with_simple_scope

        _, response = sanic_app.test_client.get("/scoped_empty")
        assert response.status == 401
        assert response.json.get("exception") == "Unauthorized"
        assert "Authorization header not present." in response.json.get(
            "reasons"
        )
