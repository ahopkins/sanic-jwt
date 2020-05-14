from sanic import Sanic
from sanic.response import json

from sanic_jwt import Authentication, exceptions, Initialize


class MyAuthentication(Authentication):
    async def authenticate(self, request, *args, **kwargs):
        username = request.json.get("username", None)
        password = request.json.get("password", None)

        if not username or not password:
            raise exceptions.AuthenticationFailed(
                "Missing username or password."
            )

        return {"user_id": 1}

    async def store_refresh_token(
        self, user_id, refresh_token, *args, **kwargs
    ):
        key = "refresh_token_{user_id}".format(user_id=user_id)
        self.app.my_cache[key] = refresh_token

    async def retrieve_refresh_token(self, user_id, *args, **kwargs):
        key = "refresh_token_{user_id}".format(user_id=user_id)
        token = self.app.my_cache.get(key, None)
        return token

    async def retrieve_user(self, request, payload, *args, **kwargs):
        if payload:
            user_id = payload.get("user_id", None)
            return {"user_id": user_id}

        else:
            return None


# elsewhere in the universe ...
if __name__ == "__main__":
    app = Sanic(__name__)
    app.my_cache = {}

    sanicjwt = Initialize(
        app, authentication_class=MyAuthentication, refresh_token_enabled=True
    )

    @app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @app.route("/protected")
    @sanicjwt.protected()
    async def protected_request(request):
        return json({"protected": True})

    # this route is for demonstration only

    @app.route("/cache")
    @sanicjwt.protected()
    async def protected_cache(request):
        return json(request.app.my_cache)

    app.run(debug=True, port=8888)
