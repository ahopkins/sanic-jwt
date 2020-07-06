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

Now, anyone can access the ``/`` route. But, only users that pass a valid access token can reach ``/protected``.

If you have initialized Sanic JWT on a ``Blueprint``, then you will need to pass the instance of that blueprint into the ``@protected`` decorator.

.. code-block:: python

    bp = Blueprint('Users')
    Initialize(bp, app=app)

    @bp.get('/users/<id>')
    @protected(bp)
    async def users(request, id):
        ...

Alternatively (and probably preferably), you can also access the decorator from the ``Initialize`` instance. This makes it easier if you forget to pass the ``Blueprint``.

.. code-block:: python

    bp = Blueprint('Users')
    sanicjwt = Initialize(bp, app=app)

    @bp.get('/users/<id>')
    @sanicjwt.protected()
    async def users(request, id):
        ...


~~~~~~~~~~~~~~~~~
Class based views
~~~~~~~~~~~~~~~~~

Using the standard `Sanic methodology <http://sanic.readthedocs.io/en/latest/sanic/class_based_views.html>`_, you can protect class based views with the same decorator.

.. code-block:: python

    class PublicView(HTTPMethodView):
    def get(self, request):
        return json({"protected": False})


    class ProtectedView(HTTPMethodView):
        decorators = [protected()]

        async def get(self, request):
            return json({"protected": True})

    app.add_route(PublicView.as_view(), '/')
    app.add_route(ProtectedView.as_view(), '/protected')

------------

+++++++++++++++++
Passing the Token
+++++++++++++++++

There are two general methodologies for passing a token: cookie based, and header based. By default, Sanic JWT will expect you to send tokens thru HTTP headers. ::

    curl -X GET -H "Authorization: Bearer <JWT>" http://localhost:8000/auth/me


~~~~~~~~~~~~~
Header Tokens
~~~~~~~~~~~~~

Header tokens are passed by adding an ``Authorization`` header that consists of two parts:

1. the word ``Bearer``
2. the JWT access token

If you would like, you can modify this behavior by changing the :doc:`configuration<configuration>` for ``authorization_header`` and ``authorization_header_prefix``.

.. code-block:: python

    Initialize(
        app,
        authorization_header='somecustomheader',
        authorization_header_prefix='MeFirst',)

::

    curl -X GET -H "somecustomheader: MeFirst <JWT>" http://localhost:8000/auth/me


~~~~~~~~~~~~~
Cookie Tokens
~~~~~~~~~~~~~

If you would like to use tokens in cookies instead of headers, you need to first set ``cookie_set=True``

.. code-block:: python

    Initialize(app, cookie_set=True)

Now, Sanic JWT will reject any request that does not have a valid access token in its cookie. As the developer, you can control how the cookie is generated with the following settings:

| ``cookie_domain`` - changes domain associated with a cooke (defaults to '')
| ``cookie_httponly`` - whether to set an httponly flag on the cookie (defaults to ``True``)
| ``cookie_access_token_name`` - the name where the cookie is stored for access token
| ``cookie_refresh_token_name`` - the name where the cookie is stored for refresh token
|

.. code-block:: python

    Initialize(
        app,
        cookie_set=True,
        cookie_domain='mydomain.com',
        cookie_httponly=False,
        cookie_access_token_name='some-token',)

.. warning::

    If you are using cookies to pass JWTs, then it is recommended that you do **not** disable ``cookie_httponly``. Doing so means that any javascript running on the client can access the token. Bad news.

**Cookie splitting, and suggested best practices**

Sanic JWT comes with the ability to split the access token into two cookies. The reason would be to allow cookies to both (1) be secured from XSS, and (2) allow for browser clients to have access to the token and it's payload.

.. note::
    
    This is initially disabled, and is an opt-in feature. However, if your intent is to use Sanic JWT with a browser based application, and you want to have access to the payload on the client, then it is **HIGHLY** suggested that you use this method, and not Header tokens.

To use split cookies, you can enable it as follows:

.. code-block:: python

    Initialize(
        app,
        cookie_set=True,
        cookie_split=True,
        cookie_access_token_name='token-header-payload',)

This will split the cookie in two parts:

1. ``header.payload``
2. ``signature``

The first part will **not** have ``HttpOnly`` set, but the signature part will. This keeps your token safe from being used since it cannot be verified by the backend. But, the payload can be accessible from JavaScript.

.. code-block:: javascript

    import jwtDecode from 'jwt-decode'

    const payload = jwtDecode(getCookieValue('token-header-payload'))

.. note::

    Setting this will override the ``cookie_httponly`` configuration for the access token. Also, the above example sets ``cookie_access_token_name``, but it is not necessary. This is just to show that ``cookie_access_token_name`` will control the name of the ``header.payload`` cookie. To change the name of the ``signature`` cookie, use ``cookie_split_signature_name``.

~~~~~~~~~~~~~~~~~~~
Query String Tokens
~~~~~~~~~~~~~~~~~~~

Sometimes, both header based authentication and cookie based authentication will not be enough. A third option is available to look for tokens inside query string arguments:

    http://localhost?access_token=<JWT>

This can be enabled with ``query_string_set=True``. One potential use for this would be authentication of a websocket endpoint where sending headers and cookies may be more challenging due to Javascript limitations.

.. warning::

    In most scenarios, it is advisable to **not** use query strings for authentication. One of the biggest reasons is that the tokens may be easily leaked if a URL is copied and pasted, or because the token may end up in server logs. However, the option is available if you need it and you feel comfortable that you can mitigate any risks.


~~~~~~~~~~~~~~~~~~~~~~
Both Header and Cookie
~~~~~~~~~~~~~~~~~~~~~~

If you enable ``cookie_set``, you will get a ``MissingAuthorizationCookie`` exception if the cookie is not present. However, sometimes you may want to fall back and look for a header token if the cookie is not there.

Is such cases, change ``cookie_strict`` to ``False``.

.. code-block:: python

    Initialize(
        app,
        cookie_set=True,
        cookie_strict=False,)

This will now tell Sanic JWT to look for the cookie first. If it is not present, before throwing an exception, it will fallback and look for an ``Authorization`` header.

~~~~~~~~~~~~~~~~~~~~
Per view declaration
~~~~~~~~~~~~~~~~~~~~

Perhaps you realize that you would like to make the declaration on a single view? Most of your views will operate using a cookie, but one particular endpoint (for whatever reason) will best be served to accept headers. Not a problem. You can simply pass in the configuration parameters right into the decorator!

.. code-block:: python

    Initialize(
        app,
        cookie_set=True,
        cookie_strict=False,)

    @app.route("/protected_by_header")
    @protected(cookie_set=False)
    async def protected_by_header_route(request):
        ...

Learn more about :doc:`configuration overrides <configuration>`.

.. note::

    This paradigm works for all configurations. Feel free to experiment and change config settings at the lowest level you might need them.

------------

+++++++++++++++++++
Advanced Decorators
+++++++++++++++++++

Want to have a greater level of control? Instead of just importing the decorators from the ``sanic_jwt.decorators`` module, you can also use the decorator directly off your initialized Sanic JWT instance!

.. code-block:: python

    sanicjwt = Initialize(app)

    @app.route("/protected")
    @sanicjwt.protected()
    async def protected_route(request):
        ...

This also works for blueprints (and has the added advantage that you no longer need to pass the `bp` instance in.


.. code-block:: python

    bp = Blueprint('Users')
    Initialize(bp, app=app)

    @bp.get('/users/<id>')
    @bp.protected()
    async def users(request, id):
        ...

.. note::

    This concept of having instance based decorators also works for the ``scoped`` decorator: ``bp.scoped('foobar')``; and the ``@inject_user`` decorator.


~~~~~~~~~~~~~~~~~~~~~~~~~~
``@inject_user`` decorator
~~~~~~~~~~~~~~~~~~~~~~~~~~

You've gone thru the hard work and added a ``retrieve_user`` method. You might as well be able to reap the benefits by leveraging that method to inject your user data into your endpoints.

.. code-block:: python

    @app.route("/protected/user")
    @inject_user()
    @protected()
    async def my_protected_user(request, user):
        return json({"user_id": user.user_id})
