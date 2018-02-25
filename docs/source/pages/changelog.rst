=========
Changelog
=========

The format is based on `Keep a Changelog <http://keepachangelog.com/en/1.0.0/>`_ and this project adheres to `Semantic Versioning <http://semver.org/spec/v2.0.0.html>`_.

++++++++++++++++++++++++++
Version 1.0.0 [2018-02-25]
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
