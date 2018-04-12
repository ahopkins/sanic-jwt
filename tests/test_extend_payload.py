from sanic import Sanic
from sanic_jwt import Initialize
from sanic_jwt import Authentication
from sanic_jwt import exceptions
import jwt


class User:
    def __init__(self, id, username, password):
        self.user_id = id
        self.username = username
        self.password = password

    def __repr__(self):
        return "User(id='{}')".format(self.user_id)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
        }


users = [
    User(1, 'user1', 'abcxyz'),
    User(2, 'user2', 'abcxyz'),
]

username_table = {u.username: u for u in users}
userid_table = {u.user_id: u for u in users}


async def authenticate(request, *args, **kwargs):
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if not username or not password:
        raise exceptions.AuthenticationFailed("Missing username or password.")

    user = username_table.get(username, None)
    if user is None:
        raise exceptions.AuthenticationFailed("User not found.")

    if password != user.password:
        raise exceptions.AuthenticationFailed("Password is incorrect.")

    return user


def test_extend_simple():
    def my_extender(payload):
        payload.update({'foo': 'bar'})
        return payload

    app = Sanic()
    sanicjwt = Initialize(
        app,
        authenticate=authenticate,
        extend_payload=my_extender,
    )

    _, response = app.test_client.post(
        '/auth', json={
            'username': 'user1',
            'password': 'abcxyz'
        })
    assert response.status == 200

    access_token = response.json.get(
        sanicjwt.config.access_token_name(), None)
    payload = jwt.decode(access_token, sanicjwt.config.secret())

    assert 'foo' in payload
    assert payload.get('foo') == 'bar'


def test_extend_with_username():
    def my_extender(payload, user):
        username = user.to_dict().get('username')
        payload.update({'username': username})
        return payload

    app = Sanic()
    sanicjwt = Initialize(
        app,
        authenticate=authenticate,
        extend_payload=my_extender,
    )

    _, response = app.test_client.post(
        '/auth', json={
            'username': 'user1',
            'password': 'abcxyz'
        })
    assert response.status == 200

    access_token = response.json.get(
        sanicjwt.config.access_token_name(), None)
    payload = jwt.decode(access_token, sanicjwt.config.secret())

    assert 'username' in payload
    assert payload.get('username') == 'user1'


def test_extend_with_username_as_subclass():
    class MyAuthentication(Authentication):
        async def extend_payload(self, payload, user):
            username = user.to_dict().get('username')
            payload.update({'username': username})
            return payload

    app = Sanic()
    sanicjwt = Initialize(
        app,
        authenticate=authenticate,
        authentication_class=MyAuthentication,
    )

    _, response = app.test_client.post(
        '/auth', json={
            'username': 'user1',
            'password': 'abcxyz'
        })
    assert response.status == 200

    access_token = response.json.get(
        sanicjwt.config.access_token_name(), None)
    payload = jwt.decode(access_token, sanicjwt.config.secret())

    assert 'username' in payload
    assert payload.get('username') == 'user1'
