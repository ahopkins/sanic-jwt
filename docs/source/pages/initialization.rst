==============
Initialization
==============

Sanic JWT operates under the hood by creating a `Blueprint <http://sanic.readthedocs.io/en/latest/sanic/blueprints.html>`_, and attaching a few routes to your application. This is accomplished by running the ``initialize`` method.

.. code-block:: python

    from sanic_jwt import initialize
    from sanic import Sanic

    async def authenticate(request):
        return dict(user_id='some_id')

    app = Sanic()
    initialize(app, authenticate)

+++++++
Concept
+++++++

Sanic JWT is meant to add a user authentication system without requiring the developer to settle on any single user management system. This part is left up to the developer. Therefore, you (as the developer) are left with the responsibility of telling Sanic JWT how to tie into your user management system.

+++++++++++++++++++++++++
The ``initialize`` method
+++++++++++++++++++++++++

The method has **two** required arguments: ``app`` and ``authenticate``, and **four** optional arguments: ``class_views``, ``store_refresh_token``, ``retrieve_refresh_token``, ``retrieve_user``.

**Parameters**:

- ``app`` - the **instance** of your Sanic app | **REQUIRED**
- ``authenticate`` - an **awaitable** that **should** return a user object | **REQUIRED**
- ``class_views`` - a **list** of tuples mapping a path to a `class based view <http://sanic.readthedocs.io/en/latest/sanic/class_based_views.html#class-based-views>`_.
- ``store_refresh_token`` - an **awaitable** that persists a refresh token to some data storage
- ``retrieve_refresh_token`` - an **awaitable** that retrieves a refresh token from some data storage
- ``retrieve_user`` - an **awaitable** that gets a user

----------
Parameters
----------

~~~~~~~~~~~~~~~~~~~~~~~~~~~
``authenticate`` - Required
~~~~~~~~~~~~~~~~~~~~~~~~~~~

*This is a coroutine. Do not forget to add* ``async`` *before your* ``def``.

**Purpose**: Just like Django's ``authenticate`` `method <https://docs.djangoproject.com/en/2.0/ref/contrib/auth/#django.contrib.auth.backends.ModelBackend.authenticate>`_, this is responsible for taking a given ``request`` and deciding whether or not there is a valid user to be authenticated. If yes, it **should** return:

- a ``dict`` with a ``user_id`` key, **or**
- an instance with a ``user_id`` property.

If your user should **not** be authenticated, then you should `raise an exception <exceptions>`_, preferably ``AuthenticationFailed``.

**Example**:

.. code-block:: python

    async def authenticate(request, *args, **kwargs):
        username = request.json.get('username', None)
        password = request.json.get('password', None)

        if not username or not password:
            raise exceptions.AuthenticationFailed("Missing username or password.")

        user = await User.get(username=username)
        if user is None:
            raise exceptions.AuthenticationFailed("User not found.")

        if password != user.password:
            raise exceptions.AuthenticationFailed("Password is incorrect.")

        return user

    initialize(app, authenticate)

.. note:: The default is to expect ``user_id`` as a key/property. However, this is modifiable using _____________.

~~~~~~~~~~~~~~~~~~~~~~~~~~
``class_views`` - Optional
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Default**: ``None``

**Purpose**: If you would like to add additional views to the authentication module, you can add them here. They must be `class based views <http://sanic.readthedocs.io/en/latest/sanic/class_based_views.html#class-based-views>`_.

**Example**: Perhaps you would like to create a "passwordless" login. You could create a form that sends a POST with a user's email address to a ``MagicLoginHandler``. That handler sends out an email with a link to your ``/auth`` endpoint.

.. code-block:: python

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

.. note:: Your class based views will probably also need to handle preflight requests, so do not forget to add an options response.

    .. code-block:: python

        async def options(self, request):
            return response.text('', status=204)

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``store_refresh_token`` - Optional \*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Default**: ``None``

**Purpose**: It is a handler to persist a refresh token to disk. See `refresh tokens <refreshtokens>`_ for more information.

**Example**:

.. code-block:: python

    async def store_refresh_token(user_id, refresh_token, *args, **kwargs):
        key = 'refresh_token_{user_id}'.format(user_id=user_id)
        await aredis.set(key, refresh_token)

    initialize(
        app,
        authenticate=lambda: True,
        store_refresh_token=store_refresh_token,
    )

.. warning:: \* This parameter is *not* required. However, if you decide to enable refresh tokens (by setting ``SANIC_JWT_REFRESH_TOKEN_ENABLED=True``) then the application will raise a ``RefreshTokenNotImplemented`` exception if you forget to implement this.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``retrieve_refresh_token`` - Optional \*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Default**: ``None``

**Purpose**: It is a handler to retrieve refresh token from disk. See `refresh tokens <refreshtokens>`_ for more information.

**Example**:

.. code-block:: python

    async def retrieve_refresh_token(user_id, *args, **kwargs):
        key = 'refresh_token_{user_id}'.format(user_id=user_id)
        return await aredis.get(key)

    initialize(
        app,
        authenticate=lambda: True,
        retrieve_refresh_token=retrieve_refresh_token
    )

.. warning:: \* This parameter is *not* required. However, if you decide to enable refresh tokens (by setting ``SANIC_JWT_REFRESH_TOKEN_ENABLED=True``) then the application will raise a ``RefreshTokenNotImplemented`` exception if you forget to implement this.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``retrieve_user`` - Optional
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Default**: ``None``

**Purpose**: It is a handler to retrieve a user object from your application. It is used to return the user object in the ``/auth/me`` `endpoint <endpoints>`_. It should return:

- a ``dict``, **or**
- an instance with a ``to_dict`` or ``__dict__`` method.

**Example**:

.. code-block:: python

    class User(object):
        ...

        def to_dict(self):
            properties = ['user_id', 'username', 'email', 'verified']
            return {prop: getattr(self, prop, None) for prop in properties}

    async def retrieve_user(request, payload, *args, **kwargs):
        if payload:
            user_id = payload.get('user_id', None)
            user = await User.get(user_id=user_id)
            return user
        else:
            return None

    initialize(
        app,
        authenticate=lambda: True,
        retrieve_user=retrieve_user
    )

.. warning:: \* This parameter is *not* required. However, if you decide to enable refresh tokens (by setting ``SANIC_JWT_REFRESH_TOKEN_ENABLED=True``) then the application will raise a ``RefreshTokenNotImplemented`` exception if you forget to implement this.
