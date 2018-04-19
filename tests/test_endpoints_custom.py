from sanic import Sanic
from sanic.response import json

from sanic_jwt import Initialize, Authentication, BaseEndpoint

msg = "custom {} endpoint"


class MyAuthenticateEndpoint(BaseEndpoint):

    async def post(self, request, *args, **kwargs):
        return json({"hello": msg.format("authentication")})


class RetrieveUserEndpoint(BaseEndpoint):

    async def get(self, request, *args, **kwargs):
        return json({"hello": msg.format("retrieve user")})


class VerifyEndpoint(BaseEndpoint):

    async def get(self, request, *args, **kwargs):
        return json({"hello": msg.format("verify")})


class RefreshEndpoint(BaseEndpoint):

    async def post(self, request, *args, **kwargs):
        return json({"hello": msg.format("refresh")})


class MyAuthentication(Authentication):
    async def store_refresh_token(self, *args, **kwargs):
        return

    async def retrieve_refresh_token(self, *args, **kwargs):
        return

    async def authenticate(self, *args, **kwargs):
        return


endpoints = {
    "authenticate_endpoint": MyAuthenticateEndpoint,
    "refresh_endpoint": RefreshEndpoint,
    "retrieve_user_endpoint": RetrieveUserEndpoint,
    "verify_endpoint": VerifyEndpoint,
}


def test_custom_endpoints_as_args():

    app = Sanic()
    sanicjwt = Initialize(app, authentication_class=MyAuthentication, refresh_token_enabled=True, **endpoints)

    @app.route("/protected")
    @sanicjwt.protected()
    async def protected_route(request):
        return json({"protected": "perhaps"})

    _, response = app.test_client.post("/auth", json={"not": "important"})

    assert response.status == 200
    access_token = response.json.get(sanicjwt.config.access_token_name(), None)

    assert access_token is None
    assert response.json.get("hello") == msg.format("authentication")

    _, response = app.test_client.get("/auth/me")

    assert response.status == 200
    assert response.json.get("hello") == msg.format("retrieve user")

    _, response = app.test_client.get("/auth/verify")

    assert response.status == 200
    assert response.json.get("hello") == msg.format("verify")

    _, response = app.test_client.post("/auth/refresh", json={"not": "important"})

    assert response.status == 200
    assert response.json.get("hello") == msg.format("refresh")

    _, response = app.test_client.get("/protected")

    assert response.status == 401
    assert response.json.get("exception") == "Unauthorized"


# def test_custom_endpoints_as_config_args():


# def test_add_invalid_endpoint_mapping_in_config():

#     class MyAythenticationEndpoint(HTTPMethodView):

#         async def post(self, request, *args, **kwargs):
#             return json({'hello': 'world'})

#     class MyConfig(Configuration):
#         authenticate_endpoint = MyAythenticationEndpoint

#     app = Sanic()
#     with pytest.raises(exceptions.InvalidEndpointFormat):
#         Initialize(app, configuration_class=MyConfig, authenticate=lambda: True)
