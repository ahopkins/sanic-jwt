==========
Exceptions
==========

There is a standard set of exceptions that Sanic JWT uses to communicate. Here is a subset of exceptions that you may find helpful while creating your application.

- ``AuthenticationFailed``
- ``MissingAuthorizationHeader``
- ``MissingAuthorizationCookie``
- ``InvalidAuthorizationHeader``
- ``MissingRegisteredClaim``
- ``Unauthorized``

It is recommended that you use exceptions in your Sanic JWT implementation. If an exception occurs, then you can control what message to return to the client. See :doc:`endpoints` for more information.
