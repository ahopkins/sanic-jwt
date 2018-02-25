from .validators import validate_scopes
from functools import wraps
from inspect import isawaitable
from sanic import Blueprint
from . import exceptions
from sanic.exceptions import add_status_code


def protected(initialized_on=None):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            if initialized_on and isinstance(initialized_on, Blueprint):
                instance = initialized_on
            else:
                instance = request.app

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
                    "Authentication instance not found. Perhaps your used "
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


def scoped(scopes,
           require_all=True,
           require_all_actions=True,
           initialized_on=None):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            if initialized_on and isinstance(initialized_on, Blueprint):
                instance = initialized_on
            else:
                instance = request.app

            try:
                is_authenticated, status, reasons = instance.auth.is_authenticated(
                    request, *args, **kwargs)
            except AttributeError:
                raise add_status_code(500)(exceptions.SanicJWTException(
                    "Authentication instance not found. Perhaps your used "
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
