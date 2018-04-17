from sanic import Sanic
from sanic.response import json
from sanic_jwt import initialize

from sanic_jwt.decorators import scoped


app = Sanic()
initialize(app, authenticate=lambda: True)


@app.route("/scoped_empty")
@scoped("something")
async def scoped(request):
    return json({"scoped": True})


class TestEndpointsScoped(object):

    def test_scoped_empty(self):
        _, response = app.test_client.get("/scoped_empty")
        assert response.status == 401
