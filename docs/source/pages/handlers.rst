========
Handlers
========

Sanic JWT allows the developer to override some underlying behavior. You enable them by putting a dotted path to the package in ``str`` format into the :doc:`settings<settings>`. ::

    app.config.SANIC_JWT_PAYLOAD_HANDLER = 'custom.handlers.extend_payload'

------------

++++++++++++++++
Payload Handlers
++++++++++++++++

These handlers are to allow the developer to make modifications to the payload as it is being built.

-------------
Adding Scopes
-------------

| **Purpose**: If you are using the ``@scoped`` :doc:`decorator<scoped>`, then you will need a way to inject the ``payload`` with the user's scopes. It should return either a single scope, or a list of scopes. :doc:`Read about scopes<scoped>` for more information.
| **Return**: ``str`` or a ``list`` of ``str``
| **Example**:
|

.. code-block:: python

    app.config.SANIC_JWT_HANDLER_PAYLOAD_SCOPES = 'custom.handlers.my_scope_extender'

    async def my_scope_extender(user, *args, **kwargs):
        return user.scopes

.. note::

    Although the ``authenticate`` method only needs to evaluate to ``True``, it is highly recommended that it return a ``user`` instance. Assuming that it has, that ``user`` will be injected into this handler for your convenience.

-------------
Adding Claims
-------------

| **Purpose**: To add an arbitrary set of claims to the payload.
| **Return**: ``dict``
| **Example**:
|

.. code-block:: python

    from sanic_jwt.handlers import extend_payload

    app.config.SANIC_JWT_HANDLER_PAYLOAD_EXTEND = 'custom.handlers.my_foo_bar_payload_extender'

    async def my_foo_bar_payload_extender(authenticator, payload, *args, **kwargs):
        # The following line is important if you want to use iss, iat, nbf, or aud claims
        payload = extend_payload(authenticator, payload, *args, **kwargs)

        payload.update({
            'foo': 'bar'
        })

        return payload

.. warning::

    Sanic JWT a few supports a few standard claims for creation and validation. If you want to use any of these, and want Sanic JWT to handle the creation, make sure that they are included in the output of this handler. Otherwise, they will not be added to the payload.

----------
Overriding
----------

| **Purpose**: To completely override the creation of the payload.
| **Return**: ``dict``
| **Example**:
|

.. code-block:: python

    app.config.SANIC_JWT_HANDLER_PAYLOAD_EXTEND = 'custom.handlers.my_payload_override'

    async def my_payload_override(authenticator, user, *args, **kwargs):
        return ({
            'sanic_is_fast': True
        })

.. note::

    Most developers will not need to override the payload creation. However, if you would like to completely take control of the payload, you can. Just note that it should contain a claim for the ``user_id`` (see :doc:`settings<settings>` related to ``SANIC_JWT_USER_ID``).

------------

+++++++++++++++++
Response Handlers
+++++++++++++++++

`Coming soon` - Will add the ability to change the response output

------------

+++++++++++++++++++++
Verification Handlers
+++++++++++++++++++++

`Coming soon` - Will add hooks before and after a token is verified (for example, custom claim verification)
