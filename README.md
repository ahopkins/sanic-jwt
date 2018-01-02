# Sanic JWT

[![Latest PyPI version](https://img.shields.io/pypi/v/sanic-jwt.svg)](https://pypi.python.org/pypi/sanic-jwt)
[![Version status](https://img.shields.io/pypi/status/sanic-jwt.svg)](https://pypi.python.org/pypi/sanic-jwt)
[![Python versions](https://img.shields.io/pypi/pyversions/sanic-jwt.svg)](https://pypi.python.org/pypi/sanic-jwt)
[![Build Status](https://travis-ci.org/ahopkins/sanic-jwt.svg?branch=master)](https://travis-ci.org/ahopkins/sanic-jwt)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/9727756ffccd45f7bc5ad6292596e03d)](https://www.codacy.com/app/ahopkins/sanic-jwt?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ahopkins/sanic-jwt&amp;utm_campaign=Badge_Grade)

JSON Web Tokens for [Sanic](https://github.com/channelcat/sanic) applications. This project was originally inspired by [Flask JWT](https://github.com/mattupstate/flask-jwt) and [Django Rest Framework JWT](https://github.com/getBlimp/django-rest-framework-jwt), but some departing decisions have been made.

1. [Getting Started](https://github.com/ahopkins/sanic-jwt#getting-started)
1. [Authenticate](https://github.com/ahopkins/sanic-jwt#authenticate)
    1. [`class_views`](https://github.com/ahopkins/sanic-jwt#class_views)
    1. [`store_refresh_token`](https://github.com/ahopkins/sanic-jwt#store_refresh_token)
    1. [`retrieve_refresh_token`](https://github.com/ahopkins/sanic-jwt#retrieve_refresh_token)
    1. [`retrieve_user`](https://github.com/ahopkins/sanic-jwt#retrieve_user)
1. [Other initialization parameters](https://github.com/ahopkins/sanic-jwt#other-initialization-parameters)
1. [Endpoints](https://github.com/ahopkins/sanic-jwt#endpoints)
    1. [`/auth`](https://github.com/ahopkins/sanic-jwt#auth)
    1. [`/auth/verify`](https://github.com/ahopkins/sanic-jwt#authverify)
    1. [`/auth/me`](https://github.com/ahopkins/sanic-jwt#authme)
    1. [`/auth/refresh`](https://github.com/ahopkins/sanic-jwt#authrefresh)
1. [Protecting routes](https://github.com/ahopkins/sanic-jwt#protecting-routes)
1. [Scopes](https://github.com/ahopkins/sanic-jwt#scopes)
1. [Settings](https://github.com/ahopkins/sanic-jwt#settings)

## Getting Started

Install from pypi using:

    pip install sanic-jwt

In order to add __Sanic JWT__, all you need to do is initialize it by passing the `sanic_jwt.initialize` method the `Sanic()` instance, and an authentication function.

```python
from sanic_jwt import initialize

async def authenticate(request):
    return dict(user_id='some_id')

app = Sanic()
initialize(app, authenticate)
```

## Authenticate

Because Sanic (and this package) are agnostic towards whatever user management system you use, you need to tell __Sanic JWT__ how it should authenticate a user.

You __MUST__ define this method. It should take a `request` argument, and return a subscriptable object with `user_id` key or or object with `user_id` attribute (can be customized by __`SANIC_JWT_USER_ID`__, see [Settings](https://github.com/ahopkins/sanic-jwt#settings) for details).

```python
async def authenticate(request):
    return dict(user_id='some_id')
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
```

## Other initialization parameters

### __`class_views`__

Default: `None`

Purpose: If you would like to add additional views to the authentication module, you can add them here. They must be [class based views](http://sanic.readthedocs.io/en/latest/sanic/class_based_views.html). Side note, your CBV will probably also need to handle preflight requests, so do not forget to add an `options` response.

Example: The below example could be used in creating a "magic" passwordless login authentication.

    class MagicLoginHandler(HTTPMethodView):
        async def options(self, request):
            return response.text('', status=204)

        async def post(self, request):
            # create a magic login token and email it to the user

            response = {
                'magic-token': token
            }
            return json(response)

    initialize(
        app,
        authenticate=lambda: True,
        class_views=[
            ('/magic-login', MagicLoginHandler)     # The path will be relative to the url prefix (which defaults to /auth)
        ]
    )

### __`store_refresh_token`__

Default: `None`

Purpose: **Required** if `SANIC_JWT_REFRESH_TOKEN_ENABLED` is set to `True` in the config. It is a handler to **store** a refresh token. If you do not set it up, and you have enabled refresh tokens, then the application will raise a `RefreshTokenNotImplemented` exception.

Example:

    def store_refresh_token(user_id, refresh_token, *args, **kwargs):
        key = 'refresh_token_{user_id}'.format(user_id=user_id)

        async def store(key):
            await aredis.set(key, refresh_token)

        app.add_task(store(key))

    initialize(
        app,
        authenticate=lambda: True,
        store_refresh_token=store_refresh_token
    )

### __`retrieve_refresh_token`__

Default: `None`

Purpose: **Required** if `SANIC_JWT_REFRESH_TOKEN_ENABLED` is set to `True` in the config. It is a handler to **retrieve** a refresh token. If you do not set it up, and you have enabled refresh tokens, then the application will raise a `RefreshTokenNotImplemented` exception.

Example:

    def retrieve_refresh_token(user_id, *args, **kwargs):
        key = 'refresh_token_{user_id}'.format(user_id=user_id)

        async def retrieve(key):
            return await aredis.get(key)

        app.add_task(retrieve(key))

    initialize(
        app,
        authenticate=lambda: True,
        retrieve_refresh_token=retrieve_refresh_token
    )

### __`retrieve_user`__

Default: `None`

Purpose: Given a `request` and a `payload`, this is a handler to retrieve a user object from your application to be used, for example in the `/me` endpoint. It should return either a `dict` or an instance of an object that either has a `to_dict` method, or `__dict__` method.

Example:

    class User(object):
        ...

        def to_dict(self):
            properties = ['user_id', 'username', 'email', 'verified']
            return {prop: getattr(self, prop, None) for prop in properties}

    def retrieve_user(request, payload, *args, **kwargs):
        if payload:
            user_id = payload.get('user_id', None)
            user = User.get(user_id=user_id)
            return user
        else:
            return None

    initialize(
        app,
        authenticate=lambda: True,
        retrieve_user=retrieve_user
    )


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

### `/auth/me`

Methods: __GET__

Returns information about the currently authenticated user.

    curl -X GET -H "Authorization: Bearer <JWT>" http://localhost:8000/auth/me

Assuming that it is valid, the response:

    200 Response
    {
        "user_id": 123456
    }

As discussed, because the application is agnostic about your user management decisions, you need to have a user object that either is a `dict` or a object instance with a `to_dict` or `__dict__` method. The output of these methods will be used to generate the `/me` response.

### `/auth/refresh`

Methods: __POST__

Validates the refresh token, and provides back a new access token.

    curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer <JWT>" -d '{"refresh_token": "<REFRESH TOKEN>"}' http://localhost:8000/auth/refresh

The response, if the refresh token is valid.

    {
        "access_token": "<JWT>"
    }

_Note: Right now, you are required to send the access token (aka `JWT`) and the refresh token. Why? Well, it seems like a good idea to facilitate the lookup of refresh tokens by knowing against which user you are trying to look up. The alternative is to lookup the user by refresh token alone. But, with this method, we are explicitly sending the user information in the `JWT`. While there is **NO** verification of the `JWT` at this stage, it is used to pass the payload. This decision may be subject to change in the future._

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

## Scopes

In addition to protecting routes to authenticated users, they can be scoped to require one or more scopes by applying the `@scoped()` decorator.

### Requirements for a scope

A **scope** is a string that consists of two parts: *namespace*, and *action(s)*. For example, it might look like this: `user:read`.

**namespace** - A scope can have either one namespace, or no namespaces.
**action** - A scope can have either no actions, or many actions.

### Example scopes

    scope:     user
    namespace: user
    action:    --

    scope:     user:read
    namespace: user
    action:    read

    scope:     user:read:write
    namespace: user
    action:    [read, write]

    scope:     :read
    namespace: --
    action:    read

### How are scopes accepted?

In defining a scoped route, you define one or more scopes that will be acceptable. A scope is accepted if the payload contains a scope that is equal to or higher than what is required. For sake of clarity in the below explanation, `required_scope` means the scope that is required for access, and `user_scope` is the scope the payload has.

A scope is acceptable ...

- If the `required_scope` namespace and the `user_scope` namespace are equal
```
# True
required_scope = 'user'
user_scope = 'user'
```
- If the `required_scope` has actions, then the `user_scope` must be top level (no defined actions), or also has the same actions
```
# True
required_scope = 'user:read'
user_scope = 'user'

# True
required_scope = 'user:read'
user_scope = 'user:read'

# True
required_scope = 'user:read'
user_scope = 'user:read:write'

# True
required_scope = ':read'
user_scope = ':read'
```

### Examples

Here is a list of example scopes and whether they pass or not:

    required scope      user scope(s)                    outcome
    ==============      =============                    =======
    'user'              ['something']                    False
    'user'              ['user']                         True
    'user:read'         ['user']                         True
    'user:read'         ['user:read']                    True
    'user:read'         ['user:write']                   False
    'user:read'         ['user:read:write']              True
    'user'              ['user:read']                    False
    'user:read:write'   ['user:read']                    False
    'user:read:write'   ['user:read:write']              True
    'user:read:write'   ['user:write:read']              True
    'user'              ['something', 'else']            False
    'user'              ['something', 'else', 'user']    True
    'user:read'         ['something:else', 'user:read']  True
    'user:read'         ['user:read', 'something:else']  True
    ':read'             [':read']                        True
    ':read'             ['admin']                        True

### Applying `@scoped()`

In order to protect a route from being accessed by tokens without the appropriate scope(s), pass in one or more scopes:

```python
@app.route("/protected/scoped/1")
@protected()
@scoped('user')
async def protected_route1(request):
    return json({"protected": True, "scoped": True})
```

In the above example, only an access token with a payload containing a scope for `user` will be accepted (such as the payload below).

    {
        "user_id": 1,
        "scopes: ["user"]
    }

You can also define multiple scopes:

```python
@scoped(['user', 'admin'])
```

In the above example, a payload **MUST** have both the `user` and `admin` scopes defined.

But, what if we only want to require one of the scopes, and not both `user` **AND** `admin`? Easy:

```python
@scoped(['user', 'admin'], False)
```

Now, having a scope of either `user` **OR** `admin` will be acceptable.

#### Parameters

The `@scoped()` decorator takes three parameters:

    scoped(scopes, requires_all, require_all_actions)

__`scopes`__
Either a single `string`, or a `list` of strings that are the defined scopes for the route.

```python
@scoped('user')
...

# Or

@scoped(['user', 'admin'])
...
```

__`require_all`__
A `boolean` that determines whether all of the defined scopes, or just one must be satisfied. Defaults to `True`.

```python
@scoped(['user', 'admin'])
...
# A payload MUST have both 'user' and 'admin' scopes


@scoped(['user', 'admin'], require_all=False)
...
# A payload can have either 'user' or 'admin' scope
```

__`require_all_actions`__
A `boolean` that determines whether all of the actions on a defined scope, or just one must be satisfied. Defaults to `True`.

```python
@scoped(':read:write')
...
# A payload MUST have both the `:read` and `:write` actions in scope


@scoped(':read:write', require_all_actions=False)
...
# A payload can have either the `:read` or `:write` action in scope
```

### Example

See `example/scopes.py` for a full working example with various scopes and users.

## Settings

__`SANIC_JWT_ACCESS_TOKEN_NAME`__

Default: `'access_token'`

Purpose: The key to be used in the payload to identify the access token.

__`SANIC_JWT_ALGORITHM`__

Default: `'HS256'`

Purpose: The hashing algorithm used to generate the tokens. Your available options are:

- __HS256__ - HMAC using SHA-256 hash algorithm (default)
- __HS384__ - HMAC using SHA-384 hash algorithm
- __HS512__ - HMAC using SHA-512 hash algorithm
- __ES256__ - ECDSA signature algorithm using SHA-256 hash algorithm
- __ES384__ - ECDSA signature algorithm using SHA-384 hash algorithm
- __ES512__ - ECDSA signature algorithm using SHA-512 hash algorithm
- __RS256__ - RSASSA-PKCS1-v1_5 signature algorithm using SHA-256 hash algorithm
- __RS384__ - RSASSA-PKCS1-v1_5 signature algorithm using SHA-384 hash algorithm
- __RS512__ - RSASSA-PKCS1-v1_5 signature algorithm using SHA-512 hash algorithm
- __PS256__ - RSASSA-PSS signature using SHA-256 and MGF1 padding with SHA-256
- __PS384__ - RSASSA-PSS signature using SHA-384 and MGF1 padding with SHA-384
- __PS512__ - RSASSA-PSS signature using SHA-512 and MGF1 padding with SHA-512

__`SANIC_JWT_AUTHORIZATION_HEADER`__

Default: `'authorization'`

Purpose: The HTTP request header used to identify the token. See also `SANIC_JWT_AUTHORIZATION_HEADER_PREFIX`.

Example:

    Authorization: Bearer <JWT HERE>

__`SANIC_JWT_AUTHORIZATION_HEADER_PREFIX`__

Default: `'Bearer'`

Purpose: The prefix for the JWT in the HTTP request header used to identify the token. See also `SANIC_JWT_AUTHORIZATION_HEADER`.

Example:

    Authorization: Bearer <JWT HERE>

__`SANIC_JWT_AUTHORIZATION_HEADER_REFRESH_PREFIX`__

Default: `'Refresh'`

Purpose: _Not currently in use._

__`SANIC_JWT_CLAIM_AUD`__

Default: `None`

Purpose: The aud (audience) claim identifies the recipients that the JWT is intended for. Each principal intended to process the JWT MUST identify itself with a value in the audience claim. If the principal processing the claim does not identify itself with a value in the aud claim when this claim is present, then the JWT MUST be rejected. In the general case, the aud value is an array of case-sensitive strings, each commonly containing a string or URI value. In the special case when the JWT has one audience, the aud value MAY be a single case-sensitive string containing a string or URI value. Use of this claim is OPTIONAL. If you assign a `str` value, then the aud claim will be generated for all requests, and will be required to verify a token.

__`SANIC_JWT_CLAIM_IAT`__

Default: `None`, requires a `bool` value

Purpose: The iat (issued at) claim identifies the time at which the JWT was issued. This claim can be used to determine the age of the JWT. Its value will be a numeric timestamp. Use of this claim is OPTIONAL. If you assign a `True` value, then the iat claim will be generated for all requests.

__`SANIC_JWT_CLAIM_ISS`__

Default: `None`, requires a `str` value

Purpose: The iss (issuer) claim identifies the principal that issued the JWT. The iss value is a case-sensitive string usually containing a string or URI value. Use of this claim is OPTIONAL. If you assign a `str` value, then the iss claim will be generated for all requests, and will be required to verify a token.

__`SANIC_JWT_CLAIM_NBF`__

Default: `None`

Purpose: The nbf (not before) claim identifies the time before which the JWT MUST NOT be accepted for processing. The processing of the nbf claim requires that the current date/time MUST be after or equal to the not-before date/time listed in the nbf claim. Implementers MAY provide for some small leeway, usually no more than a few minutes, to account for clock skew. Its value will be a numeric timestamp. Use of this claim is OPTIONAL. If you assign a `True` value, then the nbg claim will be generated for all requests, and will be required to verify a token. If `True`, the nbf claim will be set to the current time of the generation of the token. You can modify this with two additional settings: `SANIC_JWT_CLAIM_NBF_DELTA` (the number of seconds to add to the timestamp) and `SANIC_JWT_LEEWAY` (the number of seconds of leeway you want to allow for).

__`SANIC_JWT_CLAIM_NBF_DELTA`__

Default: `0`

Purpose: The offset in _seconds_ between the moment of token generation and the moment when you would like the token to be valid in the future. See `SANIC_JWT_CLAIM_NBF` for more details.

__`SANIC_JWT_COOKIE_DOMAIN`__

Default: `''`

Purpose: Used when `SANIC_JWT_COOKIE_SET` is set to `True`. When generating the cookie, it will associate it with this domain.

__`SANIC_JWT_COOKIE_HTTPONLY`__

Default: `True`

Purpose: Used when `SANIC_JWT_COOKIE_SET` is set to `True`. It enables HTTP only cookies. **HIGHLY recommended that you do not turn this off, unless you know what you are doing.**

__`SANIC_JWT_COOKIE_SET`__

Default: `False`

Purpose: By default, the application will lookie for access tokens in the HTTP request headers. If you would instead prefer to send them through cookies, enable this to `True`.


__`SANIC_JWT_COOKIE_TOKEN_NAME`__

Default: `SANIC_JWT_ACCESS_TOKEN_NAME`, will take whatever value is set there

Purpose: The name of the cookie to be set for storing the access token if using cookie based authentication.


__`SANIC_JWT_COOKIE_REFRESH_TOKEN_NAME`__

Default: `SANIC_JWT_REFRESH_TOKEN_NAME`, will take whatever value is set there

Purpose: The name of the cookie to be set for storing the refresh token if using cookie based authentication.


__`SANIC_JWT_EXPIRATION_DELTA`__

Default: `60 * 5 * 6`

Purpose: The length of time that the access token should be valid. _Since there is **NO** way to revoke an access token, it is recommended to keep this time period short, and to enable refresh tokens (which can be revoked) to retrieve new access tokens._

__`SANIC_JWT_PAYLOAD_HANDLER`__

Default: `'sanic_jwt.handlers.build_payload'`

Purpose: A handler method used to generate a payload. If you override this method, then you must return a `dict` with a key to the user id. See `SANIC_JWT_USER_ID`. In **MOST** cases, you should not need to override this method. If you would like to add additional information into a payload, the recommended method is to use `SANIC_JWT_HANDLER_PAYLOAD_EXTEND`.

__`SANIC_JWT_HANDLER_PAYLOAD_EXTEND`__

Default: `'sanic_jwt.handlers.extend_payload'`

Purpose: A handler method used to add additional information into a payload. It takes a `payload` as an input, and returns the payload with the additional information. If you have any of the registered claims enabled (see `SANIC_JWT_CLAIM_ISS`, `SANIC_JWT_CLAIM_IAT`, `SANIC_JWT_CLAIM_NBF`, `SANIC_JWT_CLAIM_AUD`), then you must return them with this handler. Therefore, it is recommended to call `sanic_jwt.handlers.extend_payload` inside your custom handler so as to make sure they are assigned properly.

Example:

    from sanic_jwt.handlers import extend_payload

    async def my_foo_bar_payload_extender(authenticator, payload, *args, **kwargs):
        payload = extend_payload(authenticator, payload, *args, **kwargs)

        payload.update({
            'foo': 'bar'
        })

        return payload

__`SANIC_JWT_HANDLER_PAYLOAD_SCOPES`__

Default: `None`

Purpose: A handler method used to add scopes into a payload. It is a convenience method so that you do not need to extend the payload with the more verbose (yet, more flexible) `SANIC_JWT_HANDLER_PAYLOAD_EXTEND`. It should return either a `string` or a `list` of `strings` that meet the scope requirements. See the secion on Scopes for more details. Also, to make it easier for the developer, the `user` instance that is returned by the `authenticate` method is passed in as a parameter as seen below.

Example:

    async def my_scope_extender(user, *args, **kwargs):
        return user.scopes

__`SANIC_JWT_LEEWAY`__

Default: `180`

Purpose: The number of seconds of leeway that the application will use to account for slight changes in system time configurations.

__`SANIC_JWT_REFRESH_TOKEN_ENABLED`__

Default: `False`

Purpose: Whether or not you would like to generate and accept refresh tokens.

__`SANIC_JWT_REFRESH_TOKEN_NAME`__

Default: `'refresh_token'`

Purpose: The key to be used in the payload to identify the refresh token.

__`SANIC_JWT_SCOPES_NAME`__

Default: `'scopes'`

Purpose: The key to be used in the payload to identify the scopes.

__`SANIC_JWT_SECRET`__

Default: `'This is a big secret. Shhhhh'`

Purpose: When generating JWT tokens, a secret is used to uniquely identify and authenticate them. This should be a string unique to your application. Keep it safe.

__`SANIC_JWT_URL_PREFIX`__

Default: `'/auth'`

Purpose: The url prefix used for all URL endpoints. Note, the placement of `/`.


__`SANIC_JWT_USER_ID`__

Default: `'user_id'`

Purpose: The key or property of your user object that contains a user id.


__`SANIC_JWT_VERIFY_EXP`__

Default: `True`

Purpose: Whether or not to check the expiration on an access token. **IMPORTANT: Changing this to `False` means that access tokens will NOT expire. Make sure you know what you are doing before disabling this.**
