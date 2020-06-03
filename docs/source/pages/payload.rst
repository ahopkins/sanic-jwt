========
Payloads
========

:doc:`As discussed<whatisjwt>`, JWTs have a payload that is essentially a key/value store of information.

With Sanic JWT, there are three main uses of the payload:

- passing claims (See :doc:`whatisjwt` for more information)
- passing scope (See :doc:`scoped` for more information)
- passing arbitrary information to the client

+++++++++++++++
Built in Claims
+++++++++++++++

Sanic JWT ships with the capability to add, and later verify, **five** standard claims: ``exp``, ``nbf``, ``iat``, ``iss``, and ``aud``.

-----------------
Expires - ``exp``
-----------------

| **Purpose**: This claim is a timestamp that dictates when the access token will no longer be available. Because JWT access tokens cannot be invalidated after they are issued, they are typically given a short life span.
| **Enabled by default**: Yes.
|

.. warning::

    It is possible to disable token expiration. Do **NOT** do this unless you know what you are doing and why you are doing it.

    .. code-block:: python

        Initialize(app, verify_exp=False)

    Okay, great. You know what you are doing. It is still revommended that you **NOT** do this. Are you sure you know what you are doing?


------------------
Audience - ``aud``
------------------

| **Purpose**: This claim identifies what service the JWT is intended to be used with. Typically it is a URI or other identifier that says the name of the client server that is supposed to be validating the token.
| **Enabled by default**: No.
| **How to use**: Set ``claim_aud`` to a ``str``
| **Example**:
|

.. code-block:: python

    Initialize(app, claim_aud='my_client_domain.com')


-------------------
Issued at - ``iat``
-------------------

| **Purpose**: This claim is a timestamp that provides the creation time of the JWT.
| **Enabled by default**: No.
| **How to use**: Set ``claim_iat`` to ``True``
| **Example**:
|

.. code-block:: python

    Initialize(app, claim_iat=True)


----------------
Issuer - ``iss``
----------------

| **Purpose**: This claim is typically a URI or other identifier to say who created and issued the token.
| **Enabled by default**: No.
| **How to use**: Set ``claim_iss`` to a ``str``
| **Example**:
|

.. code-block:: python

    Initialize(app, claim_iss='my_server_domain.com')


--------------------
Not before - ``NBF``
--------------------

| **Purpose**: This claim is a timestamp that allows the token to be created and issued, but not yet enabled for usage until after a certain time.
| **Enabled by default**: No.
| **How to use**: Set ``claim_nbf`` to ``True``, and ``claim_nbf_delta`` to an offset in seconds
| **Example**:
|

.. code-block:: python

    Initialize(app, claim_nbf=True, claim_nbf_delta=(60 * 3))

------------

+++++++++++++
Custom Claims
+++++++++++++

Sometimes you may find a need to add claims to a JWT beyond what is built into Sanic JWT.

To do so, simply subclass ``Claim`` and register them at :doc:`initialization<initialization>` by providing the custom claim class in a list to ``custom_claims``.

.. code-block:: python

    from sanic_jwt import Claim, Initialize

    MyCustomClaim(Claim):
        key = 'foo'

        def setup(self, payload, user):
            return 'bar'

        def verify(self, value):
            return value == 'bar'

    Initialize(..., custom_claims=[MyCustomClaim])

There are three attributes that a ``Claim`` must have: ``key``, ``setup``, and ``verify``.

| ``key``: The name of the claim and the key that will be inserted into the payload.
| ``setup``: A method to be run at the time the payload is created. It should return the value of the claim.
| ``verify``: A method to be run when a token is being verified. It should return a ``boolean`` whether or not the claim has been met.
|

------------

+++++++++++++++++++
Extra Verifications
+++++++++++++++++++

Besides registering custom claims, sometimes you may find the need to do additional verifications on a payload. For example, perhaps you want to run checks that span more than one claim on the payload.

To accomplish this, you can register a list of methods (that each return a ``boolean``) at :doc:`initialization<initialization>` by providing the list to ``extra_verifications``.

.. code-block:: python

    def check_number_of_claims(payload):
        return len(payload.keys()) == 5

    extra_verifications = [check_number_of_claims]
    Initialize(
        ...,
        extra_verifications=extra_verifications
    )

------------

++++++++++++++++
Payload Handlers
++++++++++++++++

:doc:`As discussed<initialization>`, there are a few handlers on the ``Initialize`` instance that can be used to modify the payload.

-------------
Adding Scopes
-------------

| **Argument**: ``add_scopes_to_payload``
| **Purpose**: If you are using the ``@scoped`` :doc:`decorator<scoped>`, then you will need a way to inject the ``payload`` with the user's scopes. It should return either a single scope, or a list of scopes. :doc:`Read about scopes<scoped>` for more information.
| **Return**: ``str`` or a ``list`` of ``str``
| **Example**:
|

.. code-block:: python

    async def my_scope_extender(user, *args, **kwargs):
        return user.scopes

    Initialize(app, add_scopes_to_payload=my_scope_extender)

.. note::

    The return of the ``authenticate`` method will be injected into this handler as ``user`` for your convenience.

---------------------
Extending the payload
---------------------

| **Argument**: ``extend_payload``
| **Purpose**: To add an arbitrary set of claims or information to the payload.
| **Return**: ``dict``
| **Example**:
|

.. code-block:: python

    def my_foo_bar_payload_extender(payload, *args, **kwargs):
        payload.update({
            'foo': 'bar'
        })

        return payload

    Initialize(app, extend_payload=my_foo_bar_payload_extender)

+++++++++++++
Token signing
+++++++++++++

JWTs need to be digitally signed to allow for cryptographically verifying that an access token was generated by your application.

.. code-block:: python

    secret = 'XXXXXXXXXXXXXXXXXXXXXXXX'

    Initialize(
        app,
        secret=mysecret)

There are several hashing algorithms that can be used to accomplish this. Check out the :doc:`configuration` page to see which algorithms are supported, and `read this <https://pyjwt.readthedocs.io/en/latest/algorithms.html#digital-signature-algorithms>`_ for more information.

If you decide to use an RSA or an EC algorithm, then you **must** provide Sanic JWT with both a public key and a private key to handle the encoding and decoding of the tokens.

.. code-block:: python

    from pathlib import Path

    public_ec_key = Path('/path') / 'to' / 'my-ec-public-key.pem'
    private_ec_key = Path('/path') / 'to' / 'my-ec-private-key.pem'

    Initialize(
        app,
        public_key=public_ec_key,
        private_key=private_ec_key,
        algorithm='ES256')

------------------
User level secrets
------------------

Sometimes, you may find it useful to have a different secret for **every** user of your application. One advantage of this could be the ability to invalidate any existing NON-expired access token for a single user, without interrupting any of your other users. Essentially, this could be equivalent to "logging out" (albeit, JWTs are by definition stateless, so it is only mimicking session based login/logout).

To implement this:

.. code-block:: python

    async def retrieve_user_secret(user_id):
        return f"user_id|{user_id}"

    Initialize(
        app,
        user_secret_enabled=True,
        retrieve_user_secret=retrieve_user_secret,
    )

.. node::

    You must have both ``user_secret_enabled=True`` and the ``retrieve_user_secret`` handler. You **do not** need to implement it this way. You can construct the handler any other way as outlined, for example: ``authentication_class``.