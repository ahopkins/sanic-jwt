===============
Getting Started
===============

In order to add **Sanic JWT**, all you need to do is initialize an instance of ``sanic_jwt.Initialize`` with your ``Sanic()`` instance, and an :doc:`authentication function <initialization>`.

.. code-block:: python

    from sanic_jwt import Initialize

    async def authenticate(request):
        return dict(user_id='some_id')

    app = Sanic()
    Initialize(app, authenticate=authenticate)


What is an authentication function? We'll get into it later, but for now all you need to know is that it is a function **you** control that takes a ``request`` and decides if there is a valid user or not. This gives you the flexibility to roll with whatever user management system you want.

After initialization, you now will have a couple endpoints at your disposal:

* ``/auth``
* ``/auth/verify``

To obtain a token, just send a **POST** call to the ``/auth`` endpoint::

    curl -X POST http://localhost:8000/auth

You should get back a bit of JSON like this::

    {
        "access_token": "<JWT>"
    }

Want to check to make sure it is valid? ::

    curl -X GET -H "Authorization: Bearer <JWT>" http://localhost:8000/auth/verify

Your response should be this: ::

    {
        "valid": true
    }

You now have a working authentication system. Woohoo!
