==============
Refresh Tokens
==============

++++++++++++++++++++++++
What is a refresh token?
++++++++++++++++++++++++

Access tokens are disposable. Because they cannot be expired, they have a *short* lifespan. However, without a refresh token, the client would need to reauthenticate every time the access token expired. Access tokens are generated, and sent to the client. They are not persisted.

Refresh tokens solve this problem. It is a token that is stored by the server. At any time a client can send the refresh token to the server and ask for a new access token.

The server takes the refresh token, looks up in its data store to see if it is acceptable. If yes, then a new access token is stored.

------------

+++++++++++++
Configuration
+++++++++++++

Sanic JWT facilitates the creation and passing of refresh tokens. However, just like with authentication, the storage and retrieval of the tokens is left to the developer. This allows the you to decide how to persist the token, and allows you to deactivate a token at any time.

There are three steps needed:

1. Enable refresh tokens via the settings configuration (``SANIC_JWT_REFRESH_TOKEN_ENABLED``)
2. Initialize Sanic JWT with a method for storing refresh tokens (``store_refresh_token``)
3. Initialize Sanic JWT with a method for retrieving refresh tokens (``retrieve_refresh_token``)

------------

+++++++++++++++++++++++
``store_refresh_token``
+++++++++++++++++++++++

When running ``initialize``, pass it a parameter that can go to your data store and retrieve a refresh token. The method is passed ``user_id`` (which comes from the user object returned from the ``authenticate`` method), and ``refresh_token``.

It can be **either** a callable or an awaitable. Here are three different examples that all do the same thing: persist a ``refresh_token`` to Redis.

.. code-block:: python

    def store_refresh_token(user_id, refresh_token, *args, **kwargs):
        key = 'refresh_token_{user_id}'.format(user_id=user_id)

        async def store(key):
            await aredis.set(key, refresh_token)

        app.add_task(store(key))


.. code-block:: python

    async def store_refresh_token(user_id, refresh_token, *args, **kwargs):
        key = 'refresh_token_{user_id}'.format(user_id=user_id)

        await aredis.set(key, refresh_token)

.. code-block:: python

    def store_refresh_token(user_id, refresh_token, *args, **kwargs):
        key = 'refresh_token_{user_id}'.format(user_id=user_id)
        redis.set(key, refresh_token)

Then you hook it up to the initialize script like this:

.. code-block ::

    initialize(
        app,
        authenticate=lambda: True,
        store_refresh_token=store_refresh_token
    )