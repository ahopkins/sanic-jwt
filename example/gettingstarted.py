from sanic import Sanic
from sanic_jwt import Initialize


async def authenticate(request):
    return dict(user_id='some_id')

app = Sanic()
Initialize(app, authenticate=authenticate)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8888)
