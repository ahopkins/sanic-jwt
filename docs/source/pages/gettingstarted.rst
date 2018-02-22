===============
Getting Started
===============

In order to add **Sanic JWT**, all you need to do is initialize it by passing the ``sanic_jwt.initialize`` method the ``Sanic()`` instance, and an :doc:`authentication function <initialization>`.

.. code-block:: python

    from sanic_jwt import Initialize

    async def authenticate(request):
        return dict(user_id='some_id')

    app = Sanic()
    Initialize(app, authenticate)


You now will have a couple endpoints at your disposal:

* ``/auth``
* ``/auth/verify``

To obtain a token, just send a **POST** call to the ``/auth`` endpoint::

    curl -X POST http://localhost:8000/auth

You should get back a bit of JSON like this::

    {
        "access_token": "<JWT>"
    }

+++++++++++++++++++++++++++
What is new in Version 1.0?
+++++++++++++++++++++++++++

If you have been using Sanic JWT, there should really not be that much different, although under the hood **a lot** has changed. For starters, the ``initialize`` method still works. But, the new recommended way to start Sanic JWT is to use the new ``Initialize`` class as seen above.

Using this class allows you to subclass it and really dive deep into modifying and configuring your project just the way you need it. Want to change the authentication responses? No problem. Want to add some new authentication endpoints? Easy.

One of the bigger changes is that we have enabled a new way to add configuration settings. You can of course continue to set them `as reecommended by Sanic<http://sanic.readthedocs.io/en/latest/sanic/config.html>`_ by making them in all capital letters, and giving it a ``SANIC_JWT_`` prefix.

.. code-block:: python

    app.config.SANIC_JWT_ACCESS_TOKEN_NAME = 'mytoken'

Or, you can simply pass your :doc:`configurations<configuration>` into the ``Initialize`` class as keyword arguments.

.. code-block:: python

    Initialize(app, access_token_name='mytoken')

Do you need some more complicated logic, or control? Then you could

.. code-block:: python
