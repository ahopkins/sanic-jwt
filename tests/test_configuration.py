import pytest
from sanic import Sanic
from sanic_jwt import initialize, Initialize, Configuration, exceptions


def test_configuration_initialize_method_default():
    try:
        app = Sanic()
        initialize(
            app,
            authenticate=lambda: True,
        )
    except Exception as e:
        pytest.fail('Raised exception: {}'.format(e))


def test_configuration_initialize_class_default():
    try:
        app = Sanic()
        Initialize(
            app,
            authenticate=lambda: True,
        )
    except Exception as e:
        pytest.fail('Raised exception: {}'.format(e))


def test_configuration_initialize_class_app_level():
    app = Sanic()
    app.config.SANIC_JWT_ACCESS_TOKEN_NAME = 'app-level'
    sanicjwt = Initialize(
        app,
        authenticate=lambda: True,
    )

    assert app.config.SANIC_JWT_ACCESS_TOKEN_NAME == 'app-level'
    assert sanicjwt.config.access_token_name == 'app-level'


def test_configuration_initialize_class_config_level_custom_classes():
    app = Sanic()
    app.config.SANIC_JWT_ACCESS_TOKEN_NAME = 'app-level'

    class MyConfig(Configuration):
        access_token_name = 'config-level'

    class MyInitialize(Initialize):
        configuration_class = MyConfig

    sanicjwt = MyInitialize(
        app,
        authenticate=lambda: True,
    )

    assert sanicjwt.config.access_token_name == 'config-level'


def test_configuration_initialize_class_instance_level():
    app = Sanic()
    app.config.SANIC_JWT_ACCESS_TOKEN_NAME = 'app-level'

    sanicjwt = Initialize(
        app,
        authenticate=lambda: True,
        access_token_name='instance-level'
    )

    assert sanicjwt.config.access_token_name == 'instance-level'


def test_configuration_initialize_class_instance_level_custom_classes():
    app = Sanic()
    app.config.SANIC_JWT_ACCESS_TOKEN_NAME = 'app-level'

    class MyConfig(Configuration):
        access_token_name = 'config-level'

    class MyInitialize(Initialize):
        configuration_class = MyConfig

    sanicjwt = MyInitialize(
        app,
        authenticate=lambda: True,
        access_token_name='instance-level'
    )

    assert sanicjwt.config.access_token_name == 'instance-level'


def test_configuration_initialize_class_with_getter():
    app = Sanic()

    class MyConfig(Configuration):
        def set_access_token_name(self):
            return 'return-level'

    class MyInitialize(Initialize):
        configuration_class = MyConfig

    sanicjwt = MyInitialize(
        app,
        authenticate=lambda: True
    )

    assert sanicjwt.config.access_token_name == 'return-level'


def test_configuration_initialize_class_as_argument():
    app = Sanic()

    class MyConfig(Configuration):
        def set_access_token_name(self):
            return 'return-level'

    sanicjwt = Initialize(
        app,
        configuration_class=MyConfig,
        authenticate=lambda: True
    )

    assert sanicjwt.config.access_token_name == 'return-level'


def test_configuration_get_method():
    app = Sanic()

    sanicjwt = Initialize(
        app, authenticate=lambda: True
    )

    assert sanicjwt.config.get('access_token_name') == "access_token"

    with pytest.raises(exceptions.LoopNotRunning):
        assert sanicjwt.config.get("access_token_name", transient=True) == "access_token"
