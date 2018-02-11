=================
Protecting Routes
=================

The purpose of this package, beyond the creation of JWTs, is to protect routes so that only users with a valid access token can reach certain resources. Endpoints in your application can be protected using the ``@protected`` decorator.

------------

++++++++++++++++++++++++++++
The ``@protected`` decorator
++++++++++++++++++++++++++++

| **Purpose**: To protect an endpoint from being accessed without a valid access token.
| **Example**:
|

.. code-block:: python

    from sanic_jwt.decorators import protected


    @app.route("/")
    async def open_route(request):
        return json({"protected": False})


    @app.route("/protected")
    @protected()
    async def protected_route(request):
        return json({"protected": True})

Now, anyone can access the ``/`` route. But, only users that pass a valid access token can reach ``protected``.

------------

+++++++++++++++++
Class based views
+++++++++++++++++

Using the standard `Sanic methodology <http://sanic.readthedocs.io/en/latest/sanic/class_based_views.html>`_, you can protect class based views with the same decorator.

.. code-block:: python

    class PublicView(HTTPMethodView):
    def get(self, request):
        return json({"protected": False})


    class ProtectedView(HTTPMethodView):
        decorators = [protected]

        async def get(self, request):
            return json({"protected": True})

    app.add_route(PublicView.as_view(), '/')
    app.add_route(ProtectedView.as_view(), '/protected')

------------

+++++++++++++++++
Passing the Token
+++++++++++++++++

There are two methods for passing a token: cookie based, and header based. By default, Sanic JWT will expect you to send tokens thru HTTP headers. ::

    curl -X GET -H "Authorization: Bearer <JWT>" http://localhost:8000/auth/me

Header Tokens
~~~~~~~~~~~~~

Header tokens are passed by adding an ``Authorization`` header that consists of two parts:

1. the word ``Bearer``
2. the JWT access token

If you would like, you can modify this behavior by changing the :doc:`settings<settings>` for ``SANIC_JWT_AUTHORIZATION_HEADER`` and ``SANIC_JWT_AUTHORIZATION_HEADER_PREFIX``.

.. code-block:: python

    app.config.SANIC_JWT_AUTHORIZATION_HEADER = 'somecustomheader'
    app.config.SANIC_JWT_AUTHORIZATION_HEADER_PREFIX = 'MeFirst'

::

    curl -X GET -H "somecustomheader: MeFirst <JWT>" http://localhost:8000/auth/me

Cookie Tokens
~~~~~~~~~~~~~

If you would like to use tokens in cookies instead of headers, you need to first change a :doc:`setting<settings>`:

.. code-block:: python

    app.config.SANIC_JWT_COOKIE_SET = True

Now, Sanic JWT will reject any request that does not have a valid access token in its cookie. As the developer, you can control how the cookie is generated with the following settings:

| ``SANIC_JWT_COOKIE_DOMAIN`` - changes domain associated with a cooke (defaults to '')
| ``SANIC_JWT_COOKIE_HTTPONLY`` - whether to set an httponly flag on the cookie
| ``SANIC_JWT_COOKIE_TOKEN_NAME`` - the name where the cookie is stored
|

.. warning::

    If you are using cookies to pass JWTs, then it is recommended that you do not disable ``SANIC_JWT_COOKIE_HTTPONLY``. Doing so means that any javascript running on the client can access the token. Bad news.

Both Header and Cookie
~~~~~~~~~~~~~~~~~~~~~~

If you enable ``SANIC_JWT_COOKIE_SET``, you will get a ``MissingAuthorizationCookie`` exception if the cookie is not present. However, sometimes you may want to fall back and look for a header token if the cookie is not there.

Is such cases, change ``SANIC_JWT_COOKIE_STRICT`` to ``False``.

Per view declaration
~~~~~~~~~~~~~~~~~~~~

`Coming soon` - the ability to decide at the view level which token to accept
