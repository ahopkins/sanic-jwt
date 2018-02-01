==============
What is a JWT?
==============

JSON Web Tokens ("JWT") are an easy way to pass authentication information to a web-based backend system. They are easy to work with, but admittedly they can be confusing for someone who has never used them. In short, here are some key concepts you should know.

This is meant to give someone a high level overview of JWTs and a practical working knowledge of what is needed to get up and running with them in an application. For more information, I suggest you read `jwt.io <https://jwt.io/introduction/>`_.

------------

+++++++++++++++++++++++
What does it look like?
+++++++++++++++++++++++

JWTs are string of a bunch of characters: ::

    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ

Upon closer inspection, it consists of three parts separated by a ``period``: ::

    - eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
    - eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9
    - TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ

In order, these parts are the **Header**, the **Payload**, and the **Signature**.

They can be decoded using base64. ::

    The Header
    {
        "alg": "HS256",
        "typ": "JWT"
    }

    The Payload
    {
        "sub": "1234567890",
        "name": "John Doe",
        "admin": true
    }

    The Signature
    <some mess of stuff>

------------

++++++++++++++++++
The Parts of a JWT
++++++++++++++++++

First, the header contains information about how the token's is encoded, and what it is.

Third, the signature is used to verify that it came from a trusted source. It is encrypted using a secret only known to the application. The secret is **NOT** passed along inside the token, and should **NOT** be shared.

Both of these sections, you will not need to concern yourself with to get started.

The Second section is the **payload**. This bit of JSON contains key/value pairs of information. Each one of these is called (in JWT terminology) a **claim**.

In the above example, there are three claims: ``sub``, ``name``, and ``admin``.

------------

+++++++++++
The Payload
+++++++++++

As an application developer, this is where you can send information from your server that authenticated a user (with a valid user name and password, for example) to a client application that needs to know what to display for the user. You can provide it with almost any bit of information you want that fits in JSON of course. And, because of the signature, you can be comfortable that the information inside the payload has not been compromised.

.. warning::

    The payload is **readable** to anyone that gets a hold of it. **DO NOT** pass sensitive information in it.

While there are no real restrictions on what claims are inside of a JWT, there are some industry standards. Below is a list that Sanic JWT has integrated for you to easily use.

``exp`` - (short for `expires`) This claim is a timestamp dictates when the access token will no longer be available. Because JWT access tokens cannot be invalidated after they are issued, they are typically given a short life span.

``nbf`` - (short for `not before`) This claim is a timestamp that allows the token to be created and issued, but not yet enabled for usage until after a certain time.

``iat`` - (short for `issues at`) This claim is a timestamp that provides the creation time of the JWT.

``iss`` - (short for `issuer`) This claim is typically a URI or other identifier to say who created and issued the token.

``aud`` - (short for `audience`) This claim identifies what service the JWT is intended to be used with. Typically it is a URI or other identifier that says the name of the server that is supposed to be validating the token.

In addition to these claims, there is another claim that generally is important for Sanic JWT: ``user_id``. This is meant to be some unique indentification of the user that requested the token. Other than that, you are free to add whatever information you would like. See :doc:`handlers<handlers>` for information on how to modify the payload in Sanic JWT.

