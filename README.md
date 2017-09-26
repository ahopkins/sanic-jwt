# Sanic JWT

JSON Web Tokens for [Sanic](https://github.com/channelcat/sanic) applications. This project was heavily inspired by [Flask JWT](https://github.com/mattupstate/flask-jwt) and [Django Rest Framework JWT](https://github.com/getBlimp/django-rest-framework-jwt).

_NOTE: This project (as of Sept 2017) is still in active development. Not all features are yet implemented. Getting close though. Then it will be time for some candy and better documentation/examples._

## Getting Started

Install from pypi using:

    pip install sanic-jwt

In order to add __Sanic JWT__, all you need to do is initialize it by passing the `sanic_jwt.initialize` method the `Sanic()` instance, and an authentication function.

```python
from sanic_jwt import initialize

def authenticate(request):
    return True

app = Sanic()
initialize(app, authenticate)
```

## Authenticate

Because Sanic (and this package) are agnostic towards whatever user management system you use, you need to tell __Sanic JWT__ how it should authenticate a user.

You __MUST__ define this method. It should take a `request` argument, and return `True` or `False`.

```python
def authenticate(request):
    return True
```

A very basic user management system might be as follows, with its corresponding `authenticate` method:

```python
from sanic_jwt import exceptions

class User(object):
    def __init__(self, id, username, password):
        self.user_id = id
        self.username = username
        self.password = password

    def __str__(self):
        return "User(id='%s')" % self.id

users = [
    User(1, 'user1', 'abcxyz'),
    User(2, 'user2', 'abcxyz'),
]

username_table = {u.username: u for u in users}
userid_table = {u.user_id: u for u in users}

def authenticate(request, *args, **kwargs):
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
```

## Other initialization parameters

TODO

## Endpoints

### `/auth`

Methods: __POST__

Generates an access token if the `authenticate` method is `True`. Using the example above, pass it a `username` and `password` and return an access token.

    curl -X POST -H "Content-Type: application/json" -d '{"username": "<USERNAME>", "password": "<PASSWORD>"}' http://localhost:8000/auth

The response, if the user credentials are valid:

    {
        "access_token": "<JWT>"
    }

### `/auth/verify`

Methods: __GET__

Returns with whether or not a given access token is valid.

    curl -X GET -H "Authorization: Bearer <JWT>" http://localhost:8000/auth/verify

Assuming that it is valid, the response:

    200 Response
    {
        "valid": true
    }

If it is not valid, you will also be given a reason.

    400 Response
    {
        "valid": false,
        "reason": "Signature has expired"
    }

### `/auth/refresh`

Methods: __POST__

Validates the refresh token, and provides back a new access token.

    curl -X POST -H "Authorization: Refresh <REFRESH TOKEN>" http://localhost:8000/auth/refresh

The response, if the refresh token is valid.

    {
        "access_token": "<JWT>"
    }


## Protecting routes

A route can be protected behind authentication simply by applying the `@protected()` decorator.

```python
from sanic_jwt.decorators import protected


@app.route("/")
async def open_route(request):
    return json({"protected": False})


@app.route("/protected")
@protected()
async def protected_route(request):
    return json({"protected": True})
```

## Settings

`SANIC_JWT_ALGORITHM`
Default `'HS256'`

`SANIC_JWT_AUTHORIZATION_HEADER`
Default `'authorization'`

`SANIC_JWT_AUTHORIZATION_HEADER_PREFIX`
Default `'Bearer'`

`SANIC_JWT_EXPIRATION_DELTA`
Default `60 * 5 * 6`

`SANIC_JWT_PAYLOAD_HANDLER`
Default `'sanic_jwt.handlers.build_payload'`

`SANIC_JWT_SECRET`
Default `'This is a big secret. Shhhhh'`

`SANIC_JWT_USER_ID`
Default `'user_id'`

## Coming Soon

- `iss` claim
- `iat` claim
- `nbf` claim
- `aud` claim
- scope
- refresh tokens
