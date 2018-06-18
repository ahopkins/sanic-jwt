=======================
Endpoints and Responses
=======================

Sanic JWT sets itself up to run as a `Sanic Blueprint <http://sanic.readthedocs.io/en/latest/sanic/blueprints.html>`_ at the ``/auth`` path. ::

    # Default
    http://localhost:8000/auth

This is can be changed via the ``url_prefix`` setting. :doc:`See settings for more <configuration>`.

.. code-block:: python

    Initialize(app, url_prefix='/api/authentication')

All Sanic JWT endpoints will now be available at: ::

    # Custom
    http://localhost:8000/api/authentication

------------

+++++++++++++++++
Default Endpoints
+++++++++++++++++

By default, there are four endpoints that ship with Sanic JWT. You can change the path that they attach to by following configuration pattern below:

.. code-block:: python

    Initialize(
        app,
        path_to_authenticate='/my_authenticate',
        path_to_retrieve_user='/my_retrieve_user',
        path_to_verify='/my_verify',
        path_to_refresh='/my_refresh',
    )

------------
Authenticate
------------

| **Default Path**: ``/auth``
| **Acceptable Methods**: ``POST``
| **Purpose**: Generates an access token if the ``authenticate`` :doc:`method <initialization>` is **truthy**.
| **Example**:
|

Request ::

    curl -X POST -H "Content-Type: application/json" -d '{"username": "<USERNAME>", "password": "<PASSWORD>"}' http://localhost:8000/auth

Response ::

    200 Response
    {
        "access_token": "<JWT>"
    }


------------
Verification
------------

| **Default Path**: ``/auth/verify``
| **Acceptable Methods**: ``GET``
| **Purpose**: Check whether or not a given access token is valid.
| **Example**:
|

Request ::

    curl -X GET -H "Authorization: Bearer <JWT>" http://localhost:8000/auth/verify

Response ::

    200 Response
    {
        "valid": true
    }

    ## or

    400 Response
    {
        "valid": false,
        "reason": "Signature has expired"
    }

--------------------
Current User Details
--------------------

| **Default Path**: ``/auth/me``
| **Acceptable Methods**: ``GET``
| **Purpose**: Retrieve information about the currently authenticated user.
| **Example**:
|

Request ::

    curl -X GET -H "Authorization: Bearer <JWT>" http://localhost:8000/auth/me

Response ::

    200 Response
    {
        "me": {
            user_id": 123456
        }
    }

.. note::

    Because this package does not know about you user management layer, you need to have a user object that either is a ``dict`` or a python object instance with a ``to_dict()`` method. The output of these methods will be used to generate the ``/me`` response.

-------------
Refresh Token
-------------

| **Default Path**: ``/auth/refresh``
| **Acceptable Methods**: ``POST``
| **Purpose**: Ask for a new access token given an existing refresh token
| **Example**:
|

Request ::

    curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer <JWT>" -d '{"refresh_token": "<REFRESH TOKEN>"}' http://localhost:8000/auth/refresh

Response ::

    {
        "access_token": "<JWT>"
    }


.. note::

    Do not forget to supply an existing ``access_token``. Even if it is expired, you **must** send the token along so that the application can get the ``user_id`` from the token's payload and cross reference it with the ``refresh_token``. Think of it as an additional level of security. To understand why, checkout `Issue #52 <https://github.com/ahopkins/sanic-jwt/issues/52>`_.

------------

++++++++++++++++
Modify Responses
++++++++++++++++

The responses for each of the default endpoints is extendable by subclassing the ``Responses`` class, and hooking into the appropriate method. Just make sure you return a ``dict``.

Your custom ``Responses`` should be hooked up to Sanic JWT using the ``responses_class`` keyword argument on the ``Initialize`` instance.

.. code-block:: python

    from sanic_jwt import Responses

    class MyResponses(Responses):
        @staticmethod
        def extend_authenticate(request,
                                user=None,
                                access_token=None,
                                refresh_token=None):
            return {}

        @staticmethod
        def extend_retrieve_user(request, user=None, payload=None):
            return {}

        @staticmethod
        def extend_verify(request, user=None, payload=None):
            return {}

        @staticmethod
        def extend_refresh(request,
                           user=None,
                           access_token=None,
                           refresh_token=None,
                           purported_token=None,
                           payload=None):
            return {}

    Initialize(app, responses_class=MyResponses)

------------

+++++++++++++++++
Custom Endpoints
+++++++++++++++++

Sometimes you may find the need to add another endpoint to your authentication system. You can do this by hooking it up at :doc:`initialization<initialization>`.

.. code-block:: python

    from sanic_jwt import BaseEndpoint

    class MyEndpoint(BaseEndpoint):
        ...

    my_views = (
        ('/my-view', MyEndpoint),
    )

    Initialize(app, class_views=my_views)

**Example**:

What if we wanted a ``/register`` endpoint? It could easily be added like this:

.. code-block:: python

    from sanic_jwt import BaseEndpoint

    class Register(BaseEndpoint):
        async def post(self, request, *args, **kwargs):
            username = request.json.get('username', None)
            email = request.json.get('email', None)

            helper = MyCustomUserAuthHelper()
            user = helper.register_new_user(username, email)

            access_token, output = await self.responses.get_access_token_output(
                request,
                user,
                self.config,
                self.instance)

            refresh_token = await self.instance.auth.get_refresh_token(request, user)
            output.update({
                self.config.refresh_token_name(): refresh_token
            })

            response = self.responses.get_token_reponse(
                request,
                access_token,
                output,
                refresh_token=refresh_token,
                config=self.config)


            return response

    my_views = (
        ('/register', Register),
    )

    Initialize(app, class_views=my_views)

You hook up your custom endpoints at :doc:`initialization<initialization>` by providing ``Initialize`` with a ``class_views`` argument naming your endpoint and its path.

.. code-block:: python

    my_endpoints = (
        ('/path/to/endpoint', MyCustomClassBasedView)
    )

.. note::

    It must be a `class based view <http://sanic.readthedocs.io/en/latest/sanic/class_based_views.html#class-based-views>`_. While it is certainly possible to subclass Sanic's ``sanic.views.HTTPMethodView``, it is recommended that you subclass ``sanic_jwt.BaseEndpoint`` instead so you have access to:

    - ``self.instance`` (the current Sanic JWT),
    - ``self.config`` (all current configurations), and
    - ``self.responses`` (the current response class instance).

------------

++++++++++++++++++
Exception Handling
++++++++++++++++++

You can customize how Sanic JWT handles responses on an exception by subclassing the ``Responses`` class, and overriding ``exception_response``.

.. code-block:: python

    from sanic_jwt import Responses

    class MyResponses(Responses):
    @staticmethod
    def exception_response(request, exception):
        exception_message = str(exception)
        return json({
            'error': True,
            'message': f'You encountered an exception: {exception_message}'
        }, status=exception.status_code)

    Initialize(app, response_class=MyResponses)


------------

+++++++++++++
Microservices
+++++++++++++

One of the benefits of a lightweight framework like Sanic is that it makes building microservice architectures simple, and flexible. If you are building a microservice application, likely you do not want all of your services to have the ``/auth`` endpoints!

.. code-block

    http://app1.mymicroserviceapp.com/auth
    http://app2.mymicroserviceapp.com/auth
    http://app3.mymicroserviceapp.com/auth

Instead, you probably only want to authenticate against a single service, and use the token generated there among all yout services. This can be easily accomplished with the ``auth_mode=True`` :doc:`configuration`. Set it to ``True`` on your authentication service, and ``False`` everywhere else. All the decorators will still work as expected.

.. code-block:: python

    # Authentication service
    Initialize(app, authenticate=lambda: True)

    # Every other service
    Initialize(app, auth_mode=False)

Now, the ``/auth`` endpoints are only on your authentication service, but the access token can be used on ANY of your other services.

.. code-block

    http://auth.mymicroserviceapp.com/auth
    http://app1.mymicroserviceapp.com
    http://app2.mymicroserviceapp.com
    http://app3.mymicroserviceapp.com

.. note::

    This works **only** if each of the services has the same ``secret``.
