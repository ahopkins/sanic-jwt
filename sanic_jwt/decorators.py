from .validators import validate_scopes
from functools import wraps
from inspect import isawaitable
from sanic.response import json
from sanic import Blueprint


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
                    return await response
                return response

            is_authorized = instance.auth.is_authenticated(
                request, *args, **kwargs)

            if is_authorized:
                response = f(request, *args, **kwargs)
                if isawaitable(response):
                    return await response
                return response
            else:
                # the user is not authorized.
                return json({
                    'status': 'not_authorized',
                }, 403)
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

            is_authenticated = instance.auth.is_authenticated(
                request, *args, **kwargs)
            if is_authenticated:
                # Retrieve the scopes from the payload
                user_scopes = instance.auth.retrieve_scopes(request)
                if user_scopes is None:
                    # If there are no defined scopes in the payload,
                    # deny access
                    is_authorized = False
                else:
                    is_authorized = await validate_scopes(
                        request, scopes, user_scopes, require_all,
                        require_all_actions, *args, **kwargs)
            else:
                is_authorized = False

            if is_authorized:
                # the user is authorized.
                # run the handler method and return the response
                response = f(request, *args, **kwargs)
                if isawaitable(response):
                    return await response
                return response
            else:
                # the user is not authorized.
                return json({
                    'status': 'not_authorized',
                }, 403)
            # return response
        return decorated_function
    return decorator
