=========
Sanic JWT
=========

|Latest PyPI version| |Version status| |Python versions| |Build Status|
|Codacy Badge| |Documentation| Waffle.io|


Sanic JWT adds authentication protection and endpoints to `Sanic <http://sanic.readthedocs.io>`_.

It is both **easy** to get up and running, and **extensible** for the developer. It can act to :doc:`protect endpoints <pages/protected>` and also :doc:`provide authentication scoping <pages/scoped>`, all wrapped into a nice `JWT <https://jwt.io>`_.

Pick your favorite user management system, run :doc:`a single class to initialize <pages/initialization>`, and you are all set.

------------

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   pages/gettingstarted
   pages/installation
   pages/simpleusage
   pages/whatisjwt
   pages/initialization
   pages/endpoints
   pages/payload
   pages/protected
   pages/scoped
   pages/refreshtokens
   pages/exceptions
   pages/configuration
   pages/examples
   pages/contributing
   pages/changelog

------------

+++++++++++++++++++++++++++
What is new in Version 1.1?
+++++++++++++++++++++++++++

The biggest changes are under the hood relating to how configuration settings are implemented. They are now fully dynamic allowing you to not only dynamically set them at run time, but also have them evaluated at the last minute to give you flexibility when needed.

Flexibility is really the name of the game for v. 1.1. Most of the features are to enable the developer that wants to dig deeper and gain more control. For example, the ``Authentication`` now has a number of new renamed methods. Checkout the source code to see what they are (hint: they are the ones NOT with an ``_`` at the beginning.)

Checkout the changelog for a more detailed description.

+++++++++++++++++++++++++++
What is new in Version 1.0?
+++++++++++++++++++++++++++

If you have been using Sanic JWT, there should really not be that much different, although under the hood **a lot** has changed. For starters, the ``initialize`` method still works. But, the new recommended way to start Sanic JWT is to use the new ``Initialize`` class as seen above.

Using this class allows you to subclass it and really dive deep into modifying and configuring your project just the way you need it. Want to change the authentication responses? No problem. Want to add some new authentication endpoints? Easy.

One of the bigger changes is that we have enabled a new way to add configuration settings. You can of course continue to set them `as recommended by Sanic <http://sanic.readthedocs.io/en/latest/sanic/config.html>`_ by making them in all capital letters, and giving it a ``SANIC_JWT_`` prefix.

.. code-block:: python

    app.config.SANIC_JWT_ACCESS_TOKEN_NAME = 'mytoken'

Or, you can simply pass your :doc:`configurations<pages/configuration>` into the ``Initialize`` class as keyword arguments.

.. code-block:: python

    Initialize(
        app,
        access_token_name='mytoken'
    )

Do you need some more complicated logic, or control? Then perhaps you want to subclass the ``Configuration`` class.

.. code-block:: python

    class MyConfig(Configuration):
        access_token_name='mytoken'
        def get_refresh_token_name(self):
            return some_crazy_logic_to_get_token_name()

    Initialize(
        app,
        configuration_class=MyConfig
    )

The point is, with Version 1, we made the entire package extremely adaptable and extensible for you to get done what you need without making decisions for you.

Have fun, and happy coding.

.. |Latest PyPI version| image:: https://img.shields.io/pypi/v/sanic-jwt.svg
   :target: https://pypi.python.org/pypi/sanic-jwt
.. |Version status| image:: https://img.shields.io/pypi/status/sanic-jwt.svg
   :target: https://pypi.python.org/pypi/sanic-jwt
.. |Python versions| image:: https://img.shields.io/pypi/pyversions/sanic-jwt.svg
   :target: https://pypi.python.org/pypi/sanic-jwt
.. |Build Status| image:: https://travis-ci.org/ahopkins/sanic-jwt.svg?branch=master
   :target: https://travis-ci.org/ahopkins/sanic-jwt
.. |Codacy Badge| image:: https://api.codacy.com/project/badge/Grade/9727756ffccd45f7bc5ad6292596e03d
   :target: https://www.codacy.com/app/ahopkins/sanic-jwt?utm_source=github.com&utm_medium=referral&utm_content=ahopkins/sanic-jwt&utm_campaign=Badge_Grade
.. |Documentation| image:: https://readthedocs.org/projects/sanic-jwt/badge/?version=latest
   :target: http://sanic-jwt.readthedocs.io/en/latest/?badge=latest
.. |Waffle.io| image:: https://badge.waffle.io/ahopkins/sanic-jwt.svg?columns=In%20Progress
   :target: https://waffle.io/ahopkins/sanic-jwt
