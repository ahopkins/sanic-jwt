============
Simple Usage
============

Let's take a look at a real simple example on how to use Sanic JWT to see the core concepts. Suppose we have a very simple user management system that stores ``User`` objects in a ``list``. You can also access a user through a ``dict`` index on the ``user_id`` and the ``username``.

.. code-block:: python

    class User(object):
        def __init__(self, id, username, password):
            self.user_id = id
            self.username = username
            self.password = password

        def __str__(self):
            return "User(id={})".format(self.id)

    users = [
        User(1, 'user1', 'abcxyz'),
        User(2, 'user2', 'abcxyz'),
    ]

    username_table = {u.username: u for u in users}
    userid_table = {u.user_id: u for u in users}

We want to be able to pass in a **username** and a **password** to authenticate our user, and then receive back an **access token** that can be used later on to access protected (aka private) data.


To get **Sanic JWT** started, we know that we need to :doc:`initialize <initialization>` with the `;authenticate;` method. The job of this method is to take the `request` and determine if there is a valid user to be authenticated. Since the developer decides upon the user management system, it is our job to figure out what this method should do.

Very simply, since we want to pass a **username** and a **password** to authenticate our user, we just need to check that the credentials are correct. If yes, we return the user. If no, we raise an :doc:`exception <exceptions>`.

.. code-block:: python

    from sanic_jwt import exceptions

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

.. note:: In a real production setting it is advised to **not** tell the user why their authentication failed. Simply raising ``exceptions.AuthenticationFailed`` should be enough. Here, for example purposes, we added some helper messages just to make it clear where we are failing.

Our whole application now looks like this:

.. code-block:: python

    from sanic import Sanic
    from sanic_jwt import exceptions
    from sanic_jwt import initialize


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


    app = Sanic()
    initialize(
        app,
        authenticate=authenticate,
    )


    if __name__ == "__main__":
        app.run(host="127.0.0.1", port=8888)

Let's try and get an access token now: ::

    curl -iv -H "Content-Type: application/json" -d '{"username": "user1", "password": "wrongpassword"}' http://localhost:8888/auth

Here is our response: ::

    *   Trying 127.0.0.1...
    * TCP_NODELAY set
    * Connected to localhost (127.0.0.1) port 8888 (#0)
    > POST /auth HTTP/1.1
    > Host: localhost:8888
    > User-Agent: curl/7.55.1
    > Accept: */*
    > Content-Type: application/json
    > Content-Length: 50
    >
    * upload completely sent off: 50 out of 50 bytes
    < HTTP/1.1 401 Unauthorized
    HTTP/1.1 401 Unauthorized
    < Connection: keep-alive
    Connection: keep-alive
    < Keep-Alive: 60
    Keep-Alive: 60
    < Content-Length: 22
    Content-Length: 22
    < Content-Type: text/plain; charset=utf-8
    Content-Type: text/plain; charset=utf-8

    <
    * Connection #0 to host localhost left intact
    Password is incorrect.

Oops! Looks like we entered the wrong password. Let's try again: ::

    curl -iv -H "Content-Type: application/json" -d '{"username": "user1", "password": "abcxyz"}' http://localhost:8888/auth

Response: ::

    *   Trying 127.0.0.1...
    * TCP_NODELAY set
    * Connected to localhost (127.0.0.1) port 8888 (#0)
    > POST /auth HTTP/1.1
    > Host: localhost:8888
    > User-Agent: curl/7.55.1
    > Accept: */*
    > Content-Type: application/json
    > Content-Length: 43
    >
    * upload completely sent off: 43 out of 43 bytes
    < HTTP/1.1 200 OK
    HTTP/1.1 200 OK
    < Connection: keep-alive
    Connection: keep-alive
    < Keep-Alive: 60
    Keep-Alive: 60
    < Content-Length: 140
    Content-Length: 140
    < Content-Type: application/json
    Content-Type: application/json

    <
    * Connection #0 to host localhost left intact
    {"access_token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE1MTY2NTExNDB9.vmfQbfx0H8vIR6wILlLqS82bJILdwecfWlFRQuHb3Ck"}

That looks better. We can head over to `jwt.io <https://jwt.io>`_ and enter the ``access_token`` to see what the token consists of.

**Header** ::

    {
      "typ": "JWT",
      "alg": "HS256"
    }

**Payload** ::

    {
      "user_id": 1,
      "exp": 1516651140
    }

Now, we can confirm that this token works. ::

    curl -iv -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE1MTY2NTExNDB9.vmfQbfx0H8vIR6wILlLqS82bJILdwecfWlFRQuHb3Ck" http://localhost:8888/auth/verify

Response: ::

    *   Trying 127.0.0.1...
    * TCP_NODELAY set
    * Connected to localhost (127.0.0.1) port 8888 (#0)
    > GET /auth/verify HTTP/1.1
    > Host: localhost:8888
    > User-Agent: curl/7.55.1
    > Accept: */*
    > Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE1MTY2NTExNDB9.vmfQbfx0H8vIR6wILlLqS82bJILdwecfWlFRQuHb3Ck
    >
    < HTTP/1.1 200 OK
    HTTP/1.1 200 OK
    < Connection: keep-alive
    Connection: keep-alive
    < Keep-Alive: 60
    Keep-Alive: 60
    < Content-Length: 14
    Content-Length: 14
    < Content-Type: application/json
    Content-Type: application/json

    <
    * Connection #0 to host localhost left intact
    {"valid":true}

Excellent. Now that we can generate and verify tokens, we can get to work.

Best of luck creating an authentication scheme that works for you. This package was meant to be simple to use, yet highly flexible. If you have any questions about how to implement Sanic JWT (or to make it better), please `create an issue <https://github.com/ahopkins/sanic-jwt/issues>`_ or get in touch.
