import logging
from contextlib import contextmanager
from functools import wraps
from inspect import isawaitable

from sanic import Blueprint
from sanic.exceptions import add_status_code

from . import exceptions
from .cache import clear_value
# from .cache import set_value
from .validators import validate_scopes

logger = logging.getLogger(__name__)


@contextmanager
def instant_config(instance, **kwargs):
    if kwargs:
        instance.auth.config.inside_context = True
        to_clean = []
        for key, val in kwargs.items():
            if hasattr(instance.auth.config, key):
                to_clean.append(key)
                instance.auth.config.set(key, val, transient=True)
    yield
    if kwargs:
        instance.auth.config.inside_context = False
        for key in to_clean:
            clear_value(key)


def protected(initialized_on=None, **kw):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            if initialized_on and isinstance(initialized_on, Blueprint):
                instance = initialized_on
            else:
                instance = request.app

            with instant_config(instance, **kw):
                if request.method == 'OPTIONS':
                    response = f(request, *args, **kwargs)
                    if isawaitable(response):
                        response = await response
                    return response

                try:
                    is_authenticated, status, reasons = instance.auth.is_authenticated(
                        request, *args, **kwargs)
                except AttributeError:
                    raise add_status_code(500)(exceptions.SanicJWTException(
                        "Authentication instance not found. Perhaps you used "
                        "@protected without passing in a blueprint? "
                        "Try @protected(blueprint)"))
                if is_authenticated:
                    response = f(request, *args, **kwargs)
                    if isawaitable(response):
                        response = await response
                    return response
                else:
                    raise add_status_code(status)(exceptions.Unauthorized(reasons))
        return decorated_function
    return decorator


def scoped(scopes, require_all=True,
           require_all_actions=True,
           initialized_on=None, **kw):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            if initialized_on and isinstance(initialized_on, Blueprint):
                instance = initialized_on
            else:
                instance = request.app

            with instant_config(instance, **kw):

                try:
                    is_authenticated, status, reasons = instance.auth.is_authenticated(
                        request, *args, **kwargs)
                except AttributeError:
                    raise add_status_code(500)(exceptions.SanicJWTException(
                        "Authentication instance not found. Perhaps you used "
                        "@scoped without passing in a blueprint? "
                        "Try @scoped(..., initialized_on=blueprint)"))
                if is_authenticated:
                    # Retrieve the scopes from the payload
                    user_scopes = instance.auth.retrieve_scopes(request)
                    if user_scopes is None:
                        # If there are no defined scopes in the payload,
                        # deny access
                        is_authorized = False
                        status = 403
                        reasons = "Invalid scope"
                    else:
                        is_authorized = await validate_scopes(
                            request, scopes, user_scopes, require_all,
                            require_all_actions, *args, **kwargs)
                        if not is_authorized:
                            status = 403
                            reasons = "Invalid scope"
                else:
                    is_authorized = False

                if is_authorized:
                    # the user is authorized.
                    # run the handler method and return the response
                    response = f(request, *args, **kwargs)
                    if isawaitable(response):
                        response = await response
                    return response
                else:
                    raise add_status_code(status)(exceptions.Unauthorized(reasons))
                # return response
        return decorated_function
    return decorator
