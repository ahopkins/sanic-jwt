==============
Refresh Tokens
==============

++++++++++++++++++++++++
What is a refresh token?
++++++++++++++++++++++++

Access tokens are disposable. Because they cannot be expired, they have a *short* lifespan. Every time an access token expires, the client needs to reauthenticate. Access tokens are generated, and sent to the client. They are not persisted. This means that they cannot be revoked.

Refresh tokens solve these two problems. It is a token that is stored by the server. At any time a client can send the refresh token to the server and ask for a new access token.

The server takes the refresh token, looks up in its data store to see if it is acceptable. If yes, then a new access token is generated and sent to the client.

In a best practices scenario, refresh tokens and access tokens work together to provide a user friendly, yet secure, authentication environment.

------------

+++++++++++++
Configuration
+++++++++++++

Sanic JWT facilitates the creation and passing of refresh tokens. However, just like with authentication, the storage and retrieval of the tokens is left to the developer. Why? This allows the you to decide how to persist the token, and allows you to deactivate a token at any time.

There are three steps needed:

1. Enable refresh tokens via the settings configuration (``refresh_token_enabled``)
2. Initialize Sanic JWT with a method for storing refresh tokens (``store_refresh_token``)
3. Initialize Sanic JWT with a method for retrieving refresh tokens (``retrieve_refresh_token``)

------------

+++++++++++++++++++++
Enable refresh tokens
+++++++++++++++++++++

Out of the box, Sanic JWT will **not** generate refresh tokens for you. If you want to make use of them, simply enable them as you would any other :doc:`configuration`. The easiest is probably just to pass ``refresh_token_enabled`` into ``Initialize``.

.. code-block:: python

    Initialize(
        app,
        authenticate=lambda: True,
        refresh_token_enabled=True,)

------------

++++++++
Handlers
++++++++

As mentioned, there are two **required** handlers you must create if you would like to provide refresh tokens to users.

~~~~~~~~~~~~~~~~~~~~~~~~~~
1. ``store_refresh_token``
~~~~~~~~~~~~~~~~~~~~~~~~~~

When running ``Initialize``, pass it an attribute that can go to your data store and persist a refresh token. The method is passed ``user_id`` (which comes from the user object returned from the ``authenticate`` method), and ``refresh_token``.

It can be **either** a callable or an awaitable. Here are two different examples that do the same thing: persist a ``refresh_token`` to Redis.

.. code-block:: python

    async def store_refresh_token(user_id, refresh_token, *args, **kwargs):
        key = f'refresh_token_{user_id}'
        await aredis.set(key, refresh_token)

.. code-block:: python

    def store_refresh_token(user_id, refresh_token, *args, **kwargs):
        key = f'refresh_token_{user_id}'
        redis.set(key, refresh_token)

Then you hook it up to the initialize script like this:

.. code-block:: python

    Initialize(
        app,
        authenticate=lambda: True,
        store_refresh_token=store_refresh_token)

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
2. ``retrieve_refresh_token``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When running ``Initialize``, pass it an attribute that can go to your data store and retrieve a refresh token. The method is passed ``user_id`` (which comes from the user object returned from the ``authenticate`` method), and the ``request`` object to determine if it contains what is needed to retrieve a token.

It can be **either** a callable or an awaitable. Here are two different examples that all do the same thing: retrieve a ``refresh_token`` from Redis.

.. code-block:: python

    async def retrieve_refresh_token(request, user_id, *args, **kwargs):
        key = f'refresh_token_{user_id}'
        return await aredis.get(key)

.. code-block:: python

    def retrieve_refresh_token(request, user_id, *args, **kwargs):
        key = f'refresh_token_{user_id}'
        return redis.get(key)

Then you hook it up to the initialize script like this:

.. code-block:: python

    Initialize(
        app,
        authenticate=lambda: True,
        retrieve_refresh_token=retrieve_refresh_token)

------------

+++++++++++++++++++++++
Using the refresh token
+++++++++++++++++++++++

In order to get a new access token, you need to hit the refresh token endpoint. See :doc:`endpoints` for more information.

++++++++++++++++++++++++++++++++++++++
Can I have an expirable refresh token?
++++++++++++++++++++++++++++++++++++++

This question has come up a couple times in the past. Allow us to explain why this is not a feature of Sanic JWT.

When enabled, Sanic JWT issues a refresh token that is a ``utf-8`` encoded string containing 24 characters. It is **not** a JWT. Therefore, it does not have a payload and is not subject to validation.

The core of deciding whether or not to accept a refresh token is left to the developer. That is the purpose of ``store_refresh_token`` and ``retrieve_refresh_token``.

Therefore, if you would like to expire the token, then this is something for you to handle at the application layer.

For more information on this, see `Issue #34 <https://github.com/ahopkins/sanic-jwt/issues/34>`_ and `Issue #66 <https://github.com/ahopkins/sanic-jwt/issues/66>`_.

We agree. Having the control expire a token is wonderful. Having it be done automatically? Even better. But, this is something that seems better left to the individual developer to decide upon, rather than Sanic JWT making that choice for you. Our goal here is to enable the developer to build a more secure platform, not make decisions for them.

~~~~~~~~~~~~~~~~~~~~~~~
But, I really want one!
~~~~~~~~~~~~~~~~~~~~~~~

Okay, fine. If you really would like to issue a JWT, or any kind of token, you can. Sanic JWT gives you the control to override our default method of generating refresh tokens. Something like this would work:

.. code-block:: python

    import uuid

    def generate_refresh_token(*args, **kwargs):
        return str(uuid.uuid4())

    Initialize(
        ...
        generate_refresh_token=generate_refresh_token,
    )

You as the developer have the control to issue whatever you would like. If you want that refresh token to be a JWT, go for it! You will need to generate it, and then validate it in the ``retrieve_refresh_token`` handler. I'll let the exercise be up to you, but feel free to `post an issue and ask for help <https://github.com/ahopkins/sanic-jwt/issues>`_.
