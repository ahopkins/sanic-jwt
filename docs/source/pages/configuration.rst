=============
Configuration
=============

+++++++++++++++++++
How to add settings
+++++++++++++++++++

There are several ways to configure Sanic JWT depeding upon your project's complexity and use case.

-------------
The Sanic way
-------------

Any way that `Sanic <http://sanic.readthedocs.io/en/latest/sanic/config.html>`_ offers to load configration will work. Simply convert the setting name to all caps, and add the ``SANIC_JWT_`` prefix.

.. code-block:: python

    app = Sanic()
    app.config.SANIC_JWT_ACCESS_TOKEN_NAME = 'jwt'

    Initialize(app)

If you choose this approach, Sanic JWT will only know about configurations set _BEFORE_ you call ``Initialize``.

------------------------
Inline at initialization
------------------------

One of the easiest methods is to simply name the setting and value as a keyword argument on the ``Initialize`` object.

.. code-block:: python

    Initialize(
        app,
        access_token_name='jwt')

-----------------------
``Configuration`` class
-----------------------

For a more fine grain control, you can subclass the ``Configuration`` class and provide the settings as attributes on the class.

.. code-block:: python

    from sanic_jwt import Configuration

    class MyConfiguration(Configuration):
        access_token_name='jwt'

    Initialize(
        app,
        configuration_class=MyConfiguration)

What if you need to calculate a setting? No problem. Each of the settings can be declared at initialization with the ``set_<setting>()`` method.

.. code-block:: python

    from sanic_jwt import Configuration

    class MyConfiguration(Configuration):
        def set_access_token_name(self):
            return 'jwt'

    Initialize(
        app,
        configuration_class=MyConfiguration)

But, it does not need to be a callable. This works too:

.. code-block:: python

    from sanic_jwt import Configuration

    class MyConfiguration(Configuration):
        set_access_token_name = 'jwt'

    Initialize(
        app,
        configuration_class=MyConfiguration)

Okay ... need to go even **further**? You can also have a setting evaluated on each request with the ``get_<setting>()`` method:

.. code-block:: python

    auth_header_key = "x-authorization-header"

    class MyConfig(Configuration):

        def get_authorization_header(self, request):
            if auth_header_key in request.headers:
                return request.headers.get(auth_header_key)

            return "authorization"

    Initialize(
        app,
        configuration_class=MyConfig
    )

This brings up an important point. If you go with the getter method, then in order to not waste resources, it will be evaluated only **one** time per request. The output of your getter will be cached for the lifespan of that request only.

As you can see, the getter method is passed the ``request`` object as a parameter.

------------

++++++++
Settings
++++++++

---------------------
``access_token_name``
---------------------

| **Purpose**: The key to be used by the application to identify the access token.
| **Default**: ``'access_token'``
|

-------------
``algorithm``
-------------

| **Purpose**: The hashing algorithm used to generate the tokens. Your available options are listed below.
| **Default**: ``'HS256'``
|

::

    HS256 - HMAC using SHA-256 hash algorithm (default)
    HS384 - HMAC using SHA-384 hash algorithm
    HS512 - HMAC using SHA-512 hash algorithm
    ES256 - ECDSA signature algorithm using SHA-256 hash algorithm
    ES384 - ECDSA signature algorithm using SHA-384 hash algorithm
    ES512 - ECDSA signature algorithm using SHA-512 hash algorithm
    RS256 - RSASSA-PKCS1-v1_5 signature algorithm using SHA-256 hash algorithm
    RS384 - RSASSA-PKCS1-v1_5 signature algorithm using SHA-384 hash algorithm
    RS512 - RSASSA-PKCS1-v1_5 signature algorithm using SHA-512 hash algorithm
    PS256 - RSASSA-PSS signature using SHA-256 and MGF1 padding with SHA-256
    PS384 - RSASSA-PSS signature using SHA-384 and MGF1 padding with SHA-384
    PS512 - RSASSA-PSS signature using SHA-512 and MGF1 padding with SHA-512


-------------
``auth_mode``
-------------

| **Purpose**: Whether to enable the ``/auth`` endpoints or not. Helpful for microservice applications.
| **Default**: ``True``
|


------------------------
``authorization_header``
------------------------

| **Purpose**: The HTTP request header used to identify the token.
| **Default**: ``'authorization'``
|

-------------------------------
``authorization_header_prefix``
-------------------------------

| **Purpose**: The prefix for the JWT in the HTTP request header used to identify the token.
| **Default**: ``'Bearer'``
|

---------------------------------------
``authorization_header_refresh_prefix``
---------------------------------------

| **Purpose**: *Reserved. Not in use.*
| **Default**: ``'Refresh'``
|

-------------
``claim_aud``
-------------

| **Purpose**: The aud (audience) claim identifies the recipients that the JWT is intended for. Each principal intended to process the JWT MUST identify itself with a value in the audience claim. If the principal processing the claim does not identify itself with a value in the aud claim when this claim is present, then the JWT MUST be rejected. In the general case, the aud value is an array of case-sensitive strings, each commonly containing a string or URI value. In the special case when the JWT has one audience, the aud value MAY be a single case-sensitive string containing a string or URI value. Use of this claim is OPTIONAL. If you assign a str value, then the aud claim will be generated for all requests, and will be required to verify a token.
| **Default**: ``None``
|

-------------
``claim_iat``
-------------

| **Purpose**: The iat (issued at) claim identifies the time at which the JWT was issued. This claim can be used to determine the age of the JWT. Its value will be a numeric timestamp. Use of this claim is *OPTIONAL*. If you assign a ``True`` value, then the iat claim will be generated for all requests.
| **Default**: ``False``
|

-------------
``claim_iss``
-------------

| **Purpose**: The iss (issuer) claim identifies the principal that issued the JWT. The iss value is a case-sensitive string usually containing a string or URI value. Use of this claim is *OPTIONAL*. If you assign a str value, then the iss claim will be generated for all requests, and will be required to verify a token.
| **Default**: ``None``, requires a ``str`` value
|

-------------
``claim_nbf``
-------------

| **Purpose**: The nbf (not before) claim identifies the time before which the JWT MUST NOT be accepted for processing. The processing of the nbf claim requires that the current date/time MUST be after or equal to the not-before date/time listed in the nbf claim. Implementers MAY provide for some small leeway, usually no more than a few minutes, to account for clock skew. Its value will be a numeric timestamp. Use of this claim is *OPTIONAL*. If you assign a ``True`` value, then the ``nbf`` claim will be generated for all requests, and will be required to verify a token. If ``True``, the ``nbf`` claim will be set to the current time of the generation of the token. You can modify this with two additional settings: ``nbf_delta`` (the number of seconds to add to the timestamp) and ``leeway`` (the number of seconds of leeway you want to allow for).
| **Default**: ``False``
|

-------------------
``claim_nbf_delta``
-------------------

| **Purpose**: The offset in seconds between the moment of token generation and the moment when you would like the token to be valid in the future.
| **Default**: ``60 * 3``
|

----------------------------
``cookie_access_token_name``
----------------------------

| **Purpose**: The name of the cookie to be set for storing the access token if using cookie based authentication.
| **Default**: ``'access_token'``
|

-----------------
``cookie_domain``
-----------------

| **Purpose**: The domain to associate a cookie with.
| **Default**: ``''``
|

-------------------
``cookie_httponly``
-------------------

| **Purpose**: It enables HTTP only cookies. **HIGHLY recommended that you do not turn this off, unless you know what you are doing.**
| **Default**: ``True``
|

-----------------------------
``cookie_refresh_token_name``
-----------------------------

| **Purpose**: The name of the cookie to be set for storing the refresh token if using cookie based authentication.
| **Default**: ``'refresh_token'``
|

--------------
``cookie_set``
--------------

| **Purpose**:  By default, the application will look for access tokens in the HTTP request headers. If you would instead prefer to send them through cookies, enable this to ``True``.
| **Default**: ``False``
|

-----------------
``cookie_strict``
-----------------

| **Purpose**: If ``cookie_set`` is enabled, an exception will be raised if the cookie is not present. To allow for an authorization header to be used as a fallback, turn ``cookie_strict`` to ``False``.
| **Default**: ``True``
|

---------------------
``cookie_token_name``
---------------------

Alias for ``cookie_access_token_name``

---------
``debug``
---------

| **Purpose**: Used for development and testing of the package. You will likely never need this.
| **Default**: ``False``
|

---------
``do_protection``
---------

| **Purpose**: Whether or not protection should be inforced. This almost **always** should stay as ``True``, unless you know what you are doing since it will effectively render the ``@protected`` decorator useless and all traffic will be passed thru.
| **Default**: ``True``
|

--------------------
``expiration_delta``
--------------------

| **Purpose**: The length of time that the access token should be valid. `Since there is NO way to revoke an access token, it is recommended to keep this time period short, and to enable refresh tokens (which can be revoked) to retrieve new access tokens.`
| **Default**: ``60 * 5 * 6``, aka 30 minutes
|

--------------------------
``generate_refresh_token``
--------------------------

| **Purpose**: A method to create and return a refresh token.
| **Default**: ``sanic_jwt.utils.generate_refresh_token``
|

----------
``leeway``
----------

| **Purpose**: The number of seconds of leeway that the application will use to account for slight changes in system time configurations.
| **Default**: ``60 * 3``, aka 3 minutes
|

------------------------
``path_to_authenticate``
------------------------

| **Purpose**: The path to the authentication endpoint.
| **Default**: ``'/'``
|

-------------------
``path_to_refresh``
-------------------

| **Purpose**: The path to the token refresh endpoint.
| **Default**: ``'/refresh'``
|

-------------------------
``path_to_retrieve_user``
-------------------------

| **Purpose**: The path to the view current user endpoint.
| **Default**: ``'/me'``
|

------------------
``path_to_verify``
------------------

| **Purpose**: The path to the token verification endpoint.
| **Default**: ``'/verify'``
|

---------------
``private_key``
---------------

| **Purpose**: A private key used for generating web tokens, dependent upon which hashing algorithm is used.
| **Default**: ``None``
|

--------------
``public_key``
--------------

Alias for ``secret``

----------------------------------
``query_string_access_token_name``
----------------------------------

| **Purpose**: The name of the cookie to be set for storing the refresh token if using query string based authentication.
| **Default**: ``'access_token'``
|

-----------------------------------
``query_string_refresh_token_name``
-----------------------------------

| **Purpose**: The name of the cookie to be set for storing the refresh token if using query string based authentication.
| **Default**: ``'refresh_token'``
|

--------------------
``query_string_set``
--------------------

| **Purpose**:  By default, the application will look for access tokens in the HTTP request headers. If you would instead prefer to send them as a URL query string, enable this to ``True``.
| **Default**: ``False``
|

-----------------------
``query_string_strict``
-----------------------

| **Purpose**: If ``query_string_set`` is enabled, an exception will be raised if the query string is not present. To allow for an authorization header to be used as a fallback, turn ``query_string_strict`` to ``False``.
| **Default**: ``True``
|

-------------------------
``refresh_token_enabled``
-------------------------

| **Purpose**:  Whether or not you would like to generate and accept refresh tokens.
| **Default**: ``False``
|

----------------------
``refresh_token_name``
----------------------

| **Purpose**: The key to be used by the application to identify the refresh token.
| **Default**: ``'refresh_token'``
|

------------------
``scopes_enabled``
------------------

| **Purpose**:  Whether or not you would like to use the scopes module and add scopes to the payload.
| **Default**: ``False``
|

---------------
``scopes_name``
---------------

| **Purpose**: The key to be used by the application to identify the scopes in the payload.
| **Default**: ``'scopes'``
|

----------
``secret``
----------

| **Purpose**: The secret used by the hashing algorithm for generating and signing JWTs. This should be a string unique to your application. Keep it safe.
| **Default**: ``'This is a big secret. Shhhhh'``
|

------------------
``strict_slashes``
------------------

| **Purpose**: Whether to enforce strict slashes on endpoints.
| **Default**: ``False``
|

--------------
``url_prefix``
--------------

| **Purpose**: The url prefix used for all URL endpoints. Note, the placement of ``/``.
| **Default**: ``'/auth'``
|

-----------
``user_id``
-----------

| **Purpose**: The key or property of your user object that contains a user id.
| **Default**: ``'user_id'``
|

--------------
``verify_exp``
--------------

| **Purpose**: Whether or not to check the expiration on an access token.
| **Default**: ``True``
|

.. warning::

    **IMPORTANT**: Changing verify_exp to ``False`` means that access tokens will **NOT** expire. Make sure you know what you are doing before disabling this.

    This is a potential **SECURITY RISK**.
