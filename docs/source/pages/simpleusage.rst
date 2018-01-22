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


To get **Sanic JWT** started, we know that we need to :doc:`initialize <initialization>` with the `authenticate` method. The job of this method is to take the `request` and determine if there is a valid user to be authenticated. Since the developer decides upon the user management system, it is our job to figure out what this method should do.

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
