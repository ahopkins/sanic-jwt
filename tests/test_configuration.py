from sanic import Sanic
from sanic_jwt import initialize, Initialize, Configuration


def test_configuration_initialize_method_default():
    app = Sanic()
    initialize(
        app,
        authenticate=lambda: True,
    )

    assert app.config.SANIC_JWT_ACCESS_TOKEN_NAME == 'access_token'


def test_configuration_initialize_class_default():
    app = Sanic()
    Initialize(
        app,
        authenticate=lambda: True,
    )

    assert app.config.SANIC_JWT_ACCESS_TOKEN_NAME == 'access_token'


def test_configuration_initialize_class_app_level():
    app = Sanic()
    app.config.SANIC_JWT_ACCESS_TOKEN_NAME = 'app-level'
    Initialize(
        app,
        authenticate=lambda: True,
    )

    assert app.config.SANIC_JWT_ACCESS_TOKEN_NAME == 'app-level'


def test_configuration_initialize_class_config_level_custom_classes():
    app = Sanic()
    app.config.SANIC_JWT_ACCESS_TOKEN_NAME = 'app-level'

    class MyConfig(Configuration):
        access_token_name = 'config-level'

    class MyInitialize(Initialize):
        configuration_class = MyConfig

    MyInitialize(
        app,
        authenticate=lambda: True,
    )

    assert app.config.SANIC_JWT_ACCESS_TOKEN_NAME == 'config-level'


def test_configuration_initialize_class_instance_level():
    app = Sanic()
    app.config.SANIC_JWT_ACCESS_TOKEN_NAME = 'app-level'

    Initialize(
        app,
        authenticate=lambda: True,
        access_token_name='instance-level'
    )

    assert app.config.SANIC_JWT_ACCESS_TOKEN_NAME == 'instance-level'


def test_configuration_initialize_class_instance_level_custom_classes():
    app = Sanic()
    app.config.SANIC_JWT_ACCESS_TOKEN_NAME = 'app-level'

    class MyConfig(Configuration):
        access_token_name = 'config-level'

    class MyInitialize(Initialize):
        configuration_class = MyConfig

    MyInitialize(
        app,
        authenticate=lambda: True,
        access_token_name='instance-level'
    )

    assert app.config.SANIC_JWT_ACCESS_TOKEN_NAME == 'instance-level'
