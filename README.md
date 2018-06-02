# Sanic JWT

[![Latest PyPI version](https://img.shields.io/pypi/v/sanic-jwt.svg)](https://pypi.python.org/pypi/sanic-jwt)
[![Python versions](https://img.shields.io/pypi/pyversions/sanic-jwt.svg)](https://pypi.python.org/pypi/sanic-jwt)
[![Version status](https://img.shields.io/pypi/status/sanic-jwt.svg)](https://pypi.python.org/pypi/sanic-jwt)
[![MIT License](https://img.shields.io/pypi/l/sanic-jwt.svg)](https://raw.githubusercontent.com/ahopkins/sanic-jwt/dev/LICENSE)

[![Build Status](https://travis-ci.org/ahopkins/sanic-jwt.svg?branch=master)](https://travis-ci.org/ahopkins/sanic-jwt)
[![Documentation](https://readthedocs.org/projects/sanic-jwt/badge/?version=latest)](http://sanic-jwt.readthedocs.io/en/latest/?badge=latest)
[![Waffle.io](https://badge.waffle.io/ahopkins/sanic-jwt.svg?columns=In%20Progress)](https://waffle.io/ahopkins/sanic-jwt)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/9727756ffccd45f7bc5ad6292596e03d)](https://www.codacy.com/app/ahopkins/sanic-jwt?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ahopkins/sanic-jwt&amp;utm_campaign=Badge_Grade)
[![Test Coverage](https://codecov.io/gh/ahopkins/sanic-jwt/branch/dev/graph/badge.svg)](https://codecov.io/gh/ahopkins/sanic-jwt)


Sanic JWT adds authentication protection and endpoints to [Sanic].

It is both **easy** to get up and running, and **extensible** for the
developer. It can act to **protect endpoints** and also provide **authentication scoping**, all wrapped into a nice [JWT].

[Read the documentation](http://sanic-jwt.rtfd.io/) | [View the source code](https://github.com/ahopkins/sanic-jwt/)

------

**What do I do?**

It's easy: (1) install, (2) initialize, and (3) authenticate.

**Install:**

```
pip install sanic-jwt
```

  [Sanic]: http://sanic.readthedocs.io
  [JWT]: https://jwt.io

**Initialize:**

```python
from sanic import Sanic
from sanic_jwt import Initialize

def my_authenticate(request, *args, **kwargs):
    ...

app = Sanic()
Initialize(
    app,
    authenticate=my_authenticate
)
```

**Authenticate:**

    http://localhost/auth

------

**Can I customize it?**

Definitely! Sanic JWT is made to allow developers to customize the operation to fit their needs. [Check out the documentation](http://sanic-jwt.rtfd.io/) to learn how.
