from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.response import json
from sanic_jwt import Initialize
from sanic_jwt.decorators import protected

blueprint = Blueprint('Test', '/test')


@blueprint.get("/", strict_slashes=True)
@protected()
def protected_hello_world(request):
    return json({'message': 'hello world'})


async def authenticate(request, *args, **kwargs):
    return {'user_id': 1}


app = Sanic()

app.blueprint(blueprint)

sanicjwt = Initialize(
    app,
    authenticate=authenticate,
)


def test_protected_blueprint():
    _, response = app.test_client.get('/test/')

    assert response.status == 401

    _, response = app.test_client.post(
        '/auth', json={
            'username': 'user1',
            'password': 'abcxyz'
        })

    assert response.status == 200

    access_token = response.json.get(sanicjwt.config.access_token_name,
                                     None)

    assert access_token is not None

    _, response = app.test_client.get(
        '/test/',
        headers={
            'Authorization': 'Bearer {}'.format(access_token)
        })

    assert response.status == 200
    assert response.json.get('message') == 'hello world'
