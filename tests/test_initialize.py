from sanic import Blueprint
from sanic import Sanic
from sanic.response import text
from sanic.views import HTTPMethodView

import pytest

from sanic_jwt import Initialize
from sanic_jwt import exceptions
from sanic_jwt import initialize


def test_store_refresh_token_and_retrieve_refresh_token_ommitted():
    app = Sanic()
    # app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED = True

    with pytest.raises(exceptions.RefreshTokenNotImplemented):
        Initialize(
            app,
            authenticate=lambda: True,
            refresh_token_enabled=True,
        )


def test_store_refresh_token_ommitted():
    app = Sanic()
    app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED = True

    with pytest.raises(exceptions.RefreshTokenNotImplemented):
        Initialize(
            app,
            authenticate=lambda: True,
            retrieve_refresh_token=lambda: True,
        )


def test_retrieve_refresh_token_ommitted():
    app = Sanic()
    app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED = True

    with pytest.raises(exceptions.RefreshTokenNotImplemented):
        initialize(
            app,
            authenticate=lambda: True,
            store_refresh_token=lambda: True,
        )


def test_store_refresh_token_and_retrieve_refresh_token_drfined():
    app = Sanic()
    app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED = True

    initialize(
        app,
        authenticate=lambda: True,
        store_refresh_token=lambda: True,
        retrieve_refresh_token=lambda: True,
    )

    assert True


def test_invalid_classview():
    app = Sanic()

    class NotAView(object):
        pass

    with pytest.raises(exceptions.InvalidClassViewsFormat):
        initialize(
            app, authenticate=lambda: True, class_views=[(object, NotAView)])


def test_initialize_class_missing_authenticate():
    app = Sanic()

    with pytest.raises(exceptions.AuthenticateNotImplemented):
        Initialize(app)


def test_initialize_class():
    app = Sanic()
    Initialize(app, authenticate=lambda: True)

    assert True


def test_initialize_class_on_blueprint_missing_app():
    app = Sanic()
    bp = Blueprint('test')
    app.blueprint(bp)

    with pytest.raises(exceptions.InitializationFailure):
        Initialize(bp, authenticate=lambda: True)


def test_initialize_class_on_blueprint():
    app = Sanic()
    bp = Blueprint('test')
    app.blueprint(bp)

    Initialize(bp, app=app, authenticate=lambda: True)

    assert True


def test_initialize_class_on_non_app_or_bp():
    app = Sanic()

    class NotAnAppOrBP(object):
        pass

    bp = NotAnAppOrBP()

    with pytest.raises(exceptions.InitializationFailure):
        Initialize(bp, app=app, authenticate=lambda: True)


def test_initialize_class_on_multiple_blueprints():
    app = Sanic()
    bp1 = Blueprint('test1')
    app.blueprint(bp1)
    bp2 = Blueprint('test2')
    app.blueprint(bp2)

    sanicjwt1 = Initialize(bp1, app=app, authenticate=lambda: True)
    sanicjwt2 = Initialize(
        bp2, app=app, authenticate=lambda: True, access_token_name='token')

    assert sanicjwt1.config.access_token_name() == 'access_token'
    assert sanicjwt2.config.access_token_name() == 'token'


def test_initialize_class_on_app_and_blueprint():
    app = Sanic()
    bp = Blueprint('test')
    app.blueprint(bp)

    sanicjwt1 = Initialize(app, authenticate=lambda: True)
    sanicjwt2 = Initialize(
        bp, app=app, authenticate=lambda: True, access_token_name='token')

    assert sanicjwt1.config.access_token_name() == 'access_token'
    assert sanicjwt2.config.access_token_name() == 'token'


def test_initialize_class_on_blueprint_with_url_prefix():
    app = Sanic()
    bp = Blueprint('test', url_prefix='/test')
    app.blueprint(bp)

    init = Initialize(bp, app=app, authenticate=lambda: True)

    assert init._get_url_prefix() == '/test/auth'


def test_initialize_class_on_blueprint_with_url_prefix_and_config():
    app = Sanic()
    bp = Blueprint('test', url_prefix='/test')
    app.blueprint(bp)

    init = Initialize(bp, app=app, authenticate=lambda: True, url_prefix='/a')

    assert init._get_url_prefix() == '/test/a'


def test_initialize_with_custom_endpoint_not_subclassed():
    class SubclassHTTPMethodView(HTTPMethodView):
        async def options(self, request):
            return text('', status=204)

        async def get(self, request):
            return text('ok')

    app = Sanic()
    with pytest.raises(exceptions.InvalidClassViewsFormat):
        Initialize(
            app,
            authenticate=lambda: True,
            class_views=[
                ('/subclass', SubclassHTTPMethodView)
            ]
        )


def test_invalid_configuration_object():

    class MyInvalidConfiguration:
        MY_CUSTOM_SETTING = 'foo'

    app = Sanic()
    with pytest.raises(exceptions.InitializationFailure):
        Initialize(app, configuration_class=MyInvalidConfiguration)


def test_invalid_authentication_object():

    class MyInvalidAuthentication:
        async def authenticate(*args, **kwargs):
            return True

    app = Sanic()
    with pytest.raises(exceptions.InitializationFailure):
        Initialize(app, authentication_class=MyInvalidAuthentication)


def test_invalid_response_object():

    class MyInvalidResponses:
        pass

    app = Sanic()
    with pytest.raises(exceptions.InitializationFailure):
        Initialize(app, responses_class=MyInvalidResponses)


def test_initialize_compat():
    app = Sanic()

    initialize(
        app,
        lambda: True,
    )

    assert True
