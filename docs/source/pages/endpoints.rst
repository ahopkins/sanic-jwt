=========
Endpoints
=========

Sanic JWT sets itseld up to run as a `Sanic Blueprint <http://sanic.readthedocs.io/en/latest/sanic/blueprints.html>`_ at the ``/auth`` path. ::

    http://localhost:8000/auth

This is can be changed via the ``SANIC_JWT_URL_PREFIX`` setting. :doc:`See settings for more <settings>`. ::

    app.config.SANIC_JWT_URL_PREFIX = '/api/authentication'

All Sanic JWT endpoints will now be available at: ::

    http://localhost:8000/api/authentication

------------

++++++++++++
Authenticate
++++++++++++

| **Path**: ``/auth``
| **Acceptable Methods**: ``POST``
| **Purpose**: Generates an access token if the ``authenticate`` :doc:`method <initialization>` evaluates to ``True``.
| **Example**:
|

Request ::

    curl -X POST -H "Content-Type: application/json" -d '{"username": "<USERNAME>", "password": "<PASSWORD>"}' http://localhost:8000/auth

Response ::

    {
        "access_token": "<JWT>"
    }

------------

++++++++++++
Verification
++++++++++++

| **Path**: ``/auth/verify``
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

------------

++++++++++++++++++++
Current User Details
++++++++++++++++++++

| **Path**: ``/auth/me``
| **Acceptable Methods**: ``GET``
| **Purpose**: Retrieve information about the currently authenticated user.
| **Example**:
|

Request ::

    curl -X GET -H "Authorization: Bearer <JWT>" http://localhost:8000/auth/me

Response ::

    200 Response
    {
        "user_id": 123456
    }


.. note::

    Because this package does not know about you user management layer, you need to have a user object that either is a dict or a object instance with a ``to_dict()`` method (this order is respected). The output of these methods will be used to generate the ``/me`` response.

------------

+++++++++++++
Refresh Token
+++++++++++++

| **Path**: ``/auth/refresh``
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

    Do not forget to supply an existing ``access_token``. Even if it is expired, you **must** send the token along so that the application can get the ``user_id`` from the token's payload and cross reference it with the ``refresh_token``.
