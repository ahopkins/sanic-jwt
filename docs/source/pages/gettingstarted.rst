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
