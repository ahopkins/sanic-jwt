import pytest
from sanic import Sanic
from sanic.response import json

from sanic_jwt import Configuration, exceptions, initialize, Initialize
from sanic_jwt.configuration import ConfigItem


def test_configuration_initialize_method_default():
    try:
        app = Sanic("sanic-jwt-test")
        initialize(app, authenticate=lambda: True)
    except Exception as e:
        pytest.fail("Raised exception: {}".format(e))


def test_configuration_initialize_class_default():
    try:
        app = Sanic("sanic-jwt-test")
        Initialize(app, authenticate=lambda: True)
    except Exception as e:
        pytest.fail("Raised exception: {}".format(e))


def test_configuration_initialize_class_app_level():
    app = Sanic("sanic-jwt-test")
    app.config.SANIC_JWT_ACCESS_TOKEN_NAME = "app-level"
    sanicjwt = Initialize(app, authenticate=lambda: True)

    assert app.config.SANIC_JWT_ACCESS_TOKEN_NAME == "app-level"
    assert sanicjwt.config.access_token_name() == "app-level"


def test_configuration_initialize_class_config_level_custom_classes():
    app = Sanic("sanic-jwt-test")
    app.config.SANIC_JWT_ACCESS_TOKEN_NAME = "app-level"

    class MyConfig(Configuration):
        access_token_name = "config-level"

    class MyInitialize(Initialize):
        configuration_class = MyConfig

    sanicjwt = MyInitialize(app, authenticate=lambda: True)

    assert sanicjwt.config.access_token_name() == "config-level"


def test_configuration_initialize_class_instance_level():
    app = Sanic("sanic-jwt-test")
    app.config.SANIC_JWT_ACCESS_TOKEN_NAME = "app-level"

    sanicjwt = Initialize(
        app, authenticate=lambda: True, access_token_name="instance-level"
    )

    assert sanicjwt.config.access_token_name() == "instance-level"


def test_configuration_initialize_class_instance_level_custom_classes():
    app = Sanic("sanic-jwt-test")
    app.config.SANIC_JWT_ACCESS_TOKEN_NAME = "app-level"

    class MyConfig(Configuration):
        access_token_name = "config-level"

    class MyInitialize(Initialize):
        configuration_class = MyConfig

    sanicjwt = MyInitialize(
        app, authenticate=lambda: True, access_token_name="instance-level"
    )

    assert sanicjwt.config.access_token_name() == "instance-level"


def test_configuration_initialize_class_with_getter():
    app = Sanic("sanic-jwt-test")

    class MyConfig(Configuration):
        def set_access_token_name(self):
            return "return-level"

    class MyInitialize(Initialize):
        configuration_class = MyConfig

    sanicjwt = MyInitialize(app, authenticate=lambda: True)

    assert sanicjwt.config.access_token_name() == "return-level"


def test_configuration_initialize_class_as_argument():
    app = Sanic("sanic-jwt-test")

    class MyConfig(Configuration):
        def set_access_token_name(self):
            return "return-level"

    sanicjwt = Initialize(
        app, configuration_class=MyConfig, authenticate=lambda: True
    )

    assert sanicjwt.config.access_token_name() == "return-level"


def test_configuration_warning_non_callable(caplog):
    app = Sanic("sanic-jwt-test")

    class MyConfig(Configuration):
        set_access_token_name = "return-level"

    sanicjwt = Initialize(
        app, configuration_class=MyConfig, authenticate=lambda: True
    )

    for record in caplog.records:
        if record.levelname == "WARNING":
            assert (
                record.message
                == 'variable "set_access_token_name" set in Configuration is not callable'
            )

    assert sanicjwt.config.access_token_name() == "access_token"


def test_configuration_warning_non_valid_key(caplog):
    app = Sanic("sanic-jwt-test")

    Initialize(app, foobar="baz", authenticate=lambda: True)

    for record in caplog.records:
        if record.levelname == "WARNING":
            assert (
                record.message
                == "Configuration key 'foobar' found is not valid for sanic-jwt"
            )


def test_configuration_dynamic_config():
    app = Sanic("sanic-jwt-test")
    auth_header_key = "x-authorization-header"

    class MyConfig(Configuration):
        def get_authorization_header(self, request):
            if auth_header_key in request.headers:
                return request.headers.get(auth_header_key)

            return "authorization"

    async def authenticate(request, *args, **kwargs):
        return {"user_id": 1}

    sanicjwt = Initialize(
        app, configuration_class=MyConfig, authenticate=authenticate
    )

    @app.route("/protected")
    @sanicjwt.protected()
    def protected_route(request):
        return json({"protected": "yes"})

    _, response = app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    access_token = response.json.get(sanicjwt.config.access_token_name(), None)
    assert access_token is not None

    _, response = app.test_client.get(
        "/protected",
        headers={
            auth_header_key: "foobarbaz",
            "foobarbaz": "Bearer {}".format(access_token),
        },
    )

    assert response.status == 200
    assert response.json.get("protected") == "yes"

    _, response = app.test_client.get(
        "/protected",
        headers={
            sanicjwt.config.authorization_header(): "Bearer {}".format(
                access_token
            )
        },
    )

    assert response.status == 200
    assert response.json.get("protected") == "yes"


def test_deprecated_handler_payload_scopes():
    app = Sanic("sanic-jwt-test")
    app.config.SANIC_JWT_HANDLER_PAYLOAD_SCOPES = lambda *a, **kw: {}

    with pytest.raises(exceptions.InvalidConfiguration):
        Initialize(app, authenticate=lambda: True)


def test_deprecated_payload_handler():
    app = Sanic("sanic-jwt-test")
    app.config.SANIC_JWT_PAYLOAD_HANDLER = lambda *a, **kw: {}

    with pytest.raises(exceptions.InvalidConfiguration):
        Initialize(app, authenticate=lambda: True)


def test_deprecated_handler_payload_extend():
    app = Sanic("sanic-jwt-test")
    app.config.SANIC_JWT_HANDLER_PAYLOAD_EXTEND = lambda *a, **kw: {}

    with pytest.raises(exceptions.InvalidConfiguration):
        Initialize(app, authenticate=lambda: True)


def test_empty_string_authorization_prefix():
    app = Sanic("sanic-jwt-test")
    authorization_header = "custom-authorization-header"
    authorization_header_prefix = ""

    async def authenticate(request, *args, **kwargs):
        return {"user_id": 1}

    sanicjwt = Initialize(
        app,
        authenticate=authenticate,
        authorization_header=authorization_header,
        authorization_header_prefix=authorization_header_prefix,
    )

    @app.route("/protected")
    @sanicjwt.protected()
    def protected_route(request):
        return json({"protected": "yes"})

    _, response = app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    access_token = response.json.get(sanicjwt.config.access_token_name(), None)
    assert access_token is not None

    _, response = app.test_client.get(
        "/protected", headers={authorization_header: access_token}
    )

    assert response.status == 200
    assert response.json.get("protected") == "yes"

    _, response = app.test_client.get(
        "/protected",
        headers={sanicjwt.config.authorization_header(): access_token},
    )

    assert response.status == 200
    assert response.json.get("protected") == "yes"


# I don't see the following scenarios happening in real life
# but we have to test them ...


def test_configuration_custom_class_and_config_item():
    app = Sanic("sanic-jwt-test")

    class MyConfig(Configuration):
        access_token_name = ConfigItem("config-item-level")

    sanicjwt = Initialize(
        app, configuration_class=MyConfig, authenticate=lambda: True
    )

    assert sanicjwt.config.access_token_name() == "config-item-level"


def test_configuration_custom_class_and_config_item_as_method():
    app = Sanic("sanic-jwt-test")

    class MyConfig(Configuration):
        def set_access_token_name(self):
            return ConfigItem("config-item-function-level")

    sanicjwt = Initialize(
        app, configuration_class=MyConfig, authenticate=lambda: True
    )

    assert sanicjwt.config.access_token_name() == "config-item-function-level"


def test_configuration_invalid_claim():
    app = Sanic("sanic-jwt-test")

    class MyConfig(Configuration):
        claim_foo = "bar"

    sanicjwt = Initialize(
        app, configuration_class=MyConfig, authenticate=lambda: True
    )

    assert "claim_foo" not in sanicjwt.config._all_config_keys


def test_disable_protection():
    app = Sanic("sanic-jwt-test")

    async def authenticate(request, *args, **kwargs):
        return {"user_id": 1}

    sanicjwt = Initialize(app, authenticate=authenticate, do_protection=False)

    @app.route("/protected")
    @sanicjwt.protected()
    def protected_route(request):
        return json({"protected": "yes"})

    _, response = app.test_client.get("/protected")

    assert response.status == 200
    assert response.json.get("protected") == "yes"


def test_configuration_with_override():
    app = Sanic("sanic-jwt-test")

    sanicjwt = Initialize(
        app, authenticate=lambda: True, access_token_name="customtoken"
    )

    assert sanicjwt.config.access_token_name() == "customtoken"

    with app.ctx.auth.override(access_token_name="foobar"):
        assert sanicjwt.config.access_token_name() == "foobar"

    assert sanicjwt.config.access_token_name() == "customtoken"


def test_configuration_with_override_on_aliased():
    app = Sanic("sanic-jwt-test")

    sanicjwt = Initialize(
        app,
        authenticate=lambda: True,
    )

    assert sanicjwt.config.public_key() == "This is a big secret. Shhhhh"
    assert sanicjwt.config.secret() == "This is a big secret. Shhhhh"

    with app.ctx.auth.override(secret="foobar"):
        assert sanicjwt.config.public_key() == "foobar"
        assert sanicjwt.config.secret() == "foobar"

    assert sanicjwt.config.public_key() == "This is a big secret. Shhhhh"
    assert sanicjwt.config.secret() == "This is a big secret. Shhhhh"

    with app.ctx.auth.override(public_key="foobar"):
        assert sanicjwt.config.public_key() == "foobar"
        assert sanicjwt.config.secret() == "foobar"

    assert sanicjwt.config.public_key() == "This is a big secret. Shhhhh"
    assert sanicjwt.config.secret() == "This is a big secret. Shhhhh"


def test_configuration_no_set_secret():
    app = Sanic("sanic-jwt-test")

    with pytest.warns(UserWarning) as record:
        Initialize(app, authenticate=lambda: True)

    assert len(record) == 1
    assert record[0].message.args[0] == (
        "Sanic JWT was initialized using the default secret available to the "
        "public. DO NOT DEPLOY your application until you change it. "
        "See https://sanic-jwt.readthedocs.io/en/latest/pages/configuration.html#secret "
        "for more information."
    )
