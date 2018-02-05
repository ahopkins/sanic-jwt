from sanic import Sanic
from sanic.response import json

import pytest
from sanic_jwt import exceptions, initialize
from sanic_jwt.decorators import protected


class User(object):

    def __init__(self, id, username, password):
        self.user_id = id
        self.username = username
        self.password = password

    def __str__(self):
        return "User(id='%s')" % self.user_id

    def to_dict(self):
        properties = [
            'user_id',
            'username',
        ]
        return {prop: getattr(self, prop, None) for prop in properties}


@pytest.yield_fixture
def users():
    yield [
        User(1, 'user1', 'abcxyz'),
        User(2, 'user2', 'abcxyz'),
    ]


@pytest.yield_fixture
def username_table(users):
    yield {u.username: u for u in users}


@pytest.yield_fixture
def authenticate(username_table):
    async def authenticate(request, *args, **kwargs):
        username = request.json.get('username', None)
        password = request.json.get('password', None)

        if not username or not password:
            raise exceptions.AuthenticationFailed(
                "Missing username or password.")

        user = username_table.get(username, None)
        if user is None:
            raise exceptions.AuthenticationFailed("User not found.")

        if password != user.password:
            raise exceptions.AuthenticationFailed("Password is incorrect.")

        return user

    yield authenticate


@pytest.yield_fixture
def app(username_table, authenticate):

    sanic_app = Sanic()
    initialize(
        sanic_app,
        authenticate=authenticate,
    )

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    yield sanic_app
