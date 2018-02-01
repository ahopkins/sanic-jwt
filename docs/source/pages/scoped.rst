======
Scopes
======

In addition to protecting routes to authenticated users, they can be scoped to require one or more scopes by applying the ``@scoped()`` decorator. This means that only users with a particular scope can access a particular endpoint.

.. note::

    If you are using the ``@scoped`` decorator, you do **NOT** also need the ``@protected`` decorator. It is assumed that if you are scoping the endpoint, that it is also meant to be protected.

------------

+++++++++++++++++++++++++
Requirements for a scoped
+++++++++++++++++++++++++

A **scope** is a string that consists of two parts:

- `namespace`
- `actions`

For example, it might look like this: ``user:read``.

| **namespace** - A scope can have either one namespace, or no namespaces
| **action** - A scope can have either no actions, or many actions

------------

++++++++++++++
Example Scopes
++++++++++++++

::

    scope:     user
    namespace: user
    action:    --

    scope:     user:read
    namespace: user
    action:    read

    scope:     user:read:write
    namespace: user
    action:    [read, write]

    scope:     :read
    namespace: --
    action:    read

------------

++++++++++++++++++++++++
How are scopes accepted?
++++++++++++++++++++++++

In defining a scoped route, you define one or more scopes that will be acceptable.

A scope is accepted if the payload contains a scope that is **equal to or higher** than what is required.

For sake of clarity in the below explanation, ``required_scope`` means the scope that is required for access, and ``user_scope`` is the scope that the access token has in its payload.

A scope is acceptable ...

    - If the ``required_scope`` namespace and the ``user_scope`` namespace are equal ::

        # True
        required_scope = 'user'
        user_scope = 'user'

    - If the ``required_scope`` has actions, then the ``user_scope`` must be:
        - top level (no defined actions), or
        - also has the same actions

      ::

          # True
          required_scope = 'user:read'
          user_scope = 'user'

          # True
          required_scope = 'user:read'
          user_scope = 'user:read'

          # True
          required_scope = 'user:read'
          user_scope = 'user:read:write'

          # True
          required_scope = ':read'
          user_scope = ':read'

          # False
          required_scope = 'user:write'
          user_scope = 'user:read'

------------

++++++++
Examples
++++++++

Here is a list of example scopes and whether they pass or not:

::

    required scope      user scope(s)                    outcome
    ==============      =============                    =======
    'user'              ['something']                    False
    'user'              ['user']                         True
    'user:read'         ['user']                         True
    'user:read'         ['user:read']                    True
    'user:read'         ['user:write']                   False
    'user:read'         ['user:read:write']              True
    'user'              ['user:read']                    False
    'user:read:write'   ['user:read']                    False
    'user:read:write'   ['user:read:write']              True
    'user:read:write'   ['user:write:read']              True
    'user'              ['something', 'else']            False
    'user'              ['something', 'else', 'user']    True
    'user:read'         ['something:else', 'user:read']  True
    'user:read'         ['user:read', 'something:else']  True
    ':read'             [':read']                        True
    ':read'             ['admin']                        True

------------

+++++++++++++++++++++
The @scoped decorator
+++++++++++++++++++++

Basics
~~~~~~

In order to protect a route from being accessed by tokens without the appropriate scope(s), pass in one or more scopes:

.. code-block:: python

    @app.route("/protected/scoped/1")
    @scoped('user')
    async def protected_route1(request):
        return json({"protected": True, "scoped": True})

In the above example, only an access token with a payload containing a scope for ``user`` will be accepted (such as the payload below). ::

    {
        "user_id": 1,
        "scopes: ["user"]
    }

You can also define multiple scopes: ::

.. code-block:: python

    @scoped(['user', 'admin'])

In the above example with a ``['user', 'admin']`` scope, a payload **MUST** contain both ``user`` and ``admin``.

But, what if we only want to require one of the scopes, and not both ``user`` AND ``admin``? Easy: ::

.. code-block:: python

    @scoped(['user', 'admin'], False)

Now, having a scope of either ``user`` OR ``admin`` will be acceptable.

Parameters
~~~~~~~~~~

The ``@scoped()`` decorator takes three parameters:

..code-block:: python

    scoped(scopes, requires_all, require_all_actions)

``scopes`` - Required
``````````````````````

Either a single ``string``, or a ``list`` of strings that are the defined scopes for the route. Or, a ``callable`` or ``awaitable`` that returns the same.

.. code-block:: python

    @scoped('user')
    ...

    # Or

    @scoped(['user', 'admin'])
    ...

    # Or

    def get_some_scopes(request, *args, **kwargs):
        return ['user', 'admin']

    @scoped(get_some_scopes)
    ...

    # Or

    async def get_some_scopes(request, *args, **kwargs):
        return await something_that_returns_scopes()

    @scoped(get_some_scopes)
    ...

``require_all`` - Optional
``````````````````````````

A ``boolean`` that determines whether all of the **defined scopes**, or just one must be satisfied. Defaults to ``True``.

.. code-block:: python

    @scoped(['user', 'admin'])
    ...
    # A payload MUST have both 'user' and 'admin' scopes


    @scoped(['user', 'admin'], require_all=False)
    ...
    # A payload can have either 'user' or 'admin' scope

``require_all_actions`` - Optional
``````````````````````````````````

A ``boolean`` that determines whether all of the **actions** on a defined scope, or just one must be satisfied. Defaults to ``True``.

.. code-block:: python

    @scoped(':read:write')
    ...
    # A payload MUST have both the `:read` and `:write` actions in scope


    @scoped(':read:write', require_all_actions=False)
    ...
    # A payload can have either the `:read` or `:write` action in scope

+++++++
Example
+++++++

.. code-block:: python

    from sanic import Sanic
    from sanic.response import json
    from sanic_jwt import exceptions
    from sanic_jwt import initialize
    from sanic_jwt.decorators import protected
    from sanic_jwt.decorators import scoped


    class User(object):
        def __init__(self, id, username, password, scopes):
            self.user_id = id
            self.username = username
            self.password = password
            self.scopes = scopes

        def __str__(self):
            return "User(id='%s')" % self.id


    users = [
        User(1, 'user1', 'abcxyz', ['user']),
        User(2, 'user2', 'abcxyz', ['user', 'admin']),
        User(3, 'user3', 'abcxyz', ['user:read']),
        User(4, 'user4', 'abcxyz', ['client1']),
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


    async def my_scope_extender(user, *args, **kwargs):
        return user.scopes


    app = Sanic()
    initialize(
        app,
        authenticate=authenticate,
    )


    app.config.SANIC_JWT_HANDLER_PAYLOAD_SCOPES = my_scope_extender


    @app.route("/")
    async def test(request):
        return json({"hello": "world"})


    @app.route("/protected")
    @protected()
    async def protected_route(request):
        return json({"protected": True, "scoped": False})


    @app.route("/protected/scoped/1")
    @protected()
    @scoped('user')
    async def protected_route1(request):
        return json({"protected": True, "scoped": True})


    @app.route("/protected/scoped/2")
    @protected()
    @scoped('user:read')
    async def protected_route2(request):
        return json({"protected": True, "scoped": True})


    @app.route("/protected/scoped/3")
    @protected()
    @scoped(['user', 'admin'])
    async def protected_route3(request):
        return json({"protected": True, "scoped": True})


    @app.route("/protected/scoped/4")
    @protected()
    @scoped(['user', 'admin'], False)
    async def protected_route4(request):
        return json({"protected": True, "scoped": True})


    @app.route("/protected/scoped/5")
    @scoped('user')
    async def protected_route5(request):
        return json({"protected": True, "scoped": True})


    @app.route("/protected/scoped/6/<id>")
    @scoped(lambda *args, **kwargs: 'user')
    async def protected_route6(request, id):
        return json({"protected": True, "scoped": True})


    def client_id_scope(request, *args, **kwargs):
        return 'client' + kwargs.get('id')


    @app.route("/protected/scoped/7/<id>")
    @scoped(client_id_scope)
    async def protected_route7(request, id):
        return json({"protected": True, "scoped": True})


    if __name__ == "__main__":
        app.run(host="127.0.0.1", port=8888)
