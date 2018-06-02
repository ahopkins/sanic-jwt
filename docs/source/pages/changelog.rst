=========
Changelog
=========

The format is based on `Keep a Changelog <http://keepachangelog.com/en/1.0.0/>`_ and this project adheres to `Semantic Versioning <http://semver.org/spec/v2.0.0.html>`_.

+++++++++++++++++++++++++
Version 1.1 - 2018-06-03
+++++++++++++++++++++++++

| **Added**
| - New handler method: ``override_scope_validator``
| - New handler method: ``destructure_scopes``
| - New decorator method: ``inject_user``
| - Decorator methods copied to ``Initialize`` class for convenience
| - New convenience method for extracting ``user_id`` from request
| - Feature for decoupling authentication mode for microservices
| - Ability to have custom generated refresh tokens
| - Subclasses are tested for consistency on ``Initialize``
|

| **Changed**
| - ``Authentication.is_authenticated`` to ``Authentication._check_authentication``
| - ``Authentication.verify`` to ``Authentication._verify``
| - ``Authentication.get_access_token`` to ``Authentication.generate_access_token``
| - ``Authentication.get_refresh_token`` to ``Authentication.generate_refresh_token``
| - ``Authentication.retrieve_scopes`` to ``Authentication.extract_scopes``
| - Method for getting and setting configurations made dynamic
|

| **Fixed**
| - Verification that a custom payload extender supplies all of the enabled claims
| - ``abort`` bug when using Sanic's convenience method for exceptions
|


++++++++++++++++++++++++++
Version 1.0.2 - 2018-03-04
++++++++++++++++++++++++++

| **Fixed**
| - Typo in docs for refresh token page
| - Custom endpoints passing parameters to ``BaseEndpoint``
|

++++++++++++++++++++++++++
Version 1.0.1 - 2018-02-27
++++++++++++++++++++++++++

| **Added**
| - ``OPTIONS`` handler method for ``BaseEndpoint``
|

| **Fixed**
| - Some tests for claims that were not using UTC timestamps
| - Consistency of docs with ``class_views``
|

++++++++++++++++++++++++++
Version 1.0.0 - 2018-02-25
++++++++++++++++++++++++++

| **Added**
| - ``Initialize`` class
| - New methods for adding configuration settings
| - Customizable components
| - Customizable responses
| - Ability to fallback to header based authentication if cookie based fails
| - Initialize on a blueprint and isolate configuration
|

| **Fixed**
| - ``@protected`` implementation on class based views
| - Usage of signing algorithms with public and private keys
|

| **Deprecated**
| - ``SANIC_JWT_PAYLOAD_HANDLER``
| - ``SANIC_JWT_HANDLER_PAYLOAD_EXTEND``
| - ``SANIC_JWT_HANDLER_PAYLOAD_SCOPES``
|

++++++
Legend
++++++

- **Added** for new features.
- **Changed** for changes in existing functionality.
- **Deprecated** for once-stable features removed in upcoming releases.
- **Removed** for deprecated features removed in this release.
- **Fixed** for any bug fixes.
- **Security** to invite users to upgrade in case of vulnerabilities.
