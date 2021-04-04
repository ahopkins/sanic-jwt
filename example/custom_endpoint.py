from sanic import Sanic
from sanic_jwt import Initialize
from sanic_jwt import BaseEndpoint


async def authenticate(request, **kwargs):
    return dict(user_id="some_id")


async def store_refresh_token(user_id, refresh_token, *args, **kwargs):
    pass


def retrieve_refresh_token(request, user_id, *args, **kwargs):
    return "1234"


class Register(BaseEndpoint):
    async def post(self, request, *args, **kwargs):
        username = "username"
        email = "email"

        user = await authenticate(request, username=username, email=email)

        access_token, output = await self.responses.get_access_token_output(
            request, user, self.config, self.instance
        )

        refresh_token = await self.instance.ctx.auth.generate_refresh_token(
            request, user
        )
        output.update({self.config.refresh_token_name(): refresh_token})

        response = self.responses.get_token_response(
            request,
            access_token,
            output,
            refresh_token=refresh_token,
            config=self.config,
        )

        return response


my_views = (("/register", Register),)

app = Sanic()
Initialize(
    app,
    authenticate=authenticate,
    class_views=my_views,
    refresh_token_enabled=True,
    store_refresh_token=store_refresh_token,
    retrieve_refresh_token=retrieve_refresh_token,
)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8888)
