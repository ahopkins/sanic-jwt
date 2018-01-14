from functools import wraps
from sanic.response import json
from .validators import validate_scopes


def protected(*args):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            if request.method == 'OPTIONS':
                response = await f(request, *args, **kwargs)
                return response

            is_authorized = request.app.auth.is_authenticated(request, *args, **kwargs)

            if is_authorized:
                # the user is authorized.
                # run the handler method and return the response
                response = await f(request, *args, **kwargs)
                return response
            else:
                # the user is not authorized.
                return json({
                    'status': 'not_authorized',
                }, 403)
        return decorated_function
    if args:
        return decorator(*args)
    else:
        return decorator


def scoped(scopes, require_all=True, require_all_actions=True):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            is_authenticated = request.app.auth.is_authenticated(request, *args, **kwargs)
            if is_authenticated:
                # Retrieve the scopes from the payload
                user_scopes = request.app.auth.retrieve_scopes(request)
                if user_scopes is None:
                    # If there are no defined scopes in the payload, deny access
                    is_authorized = False
                else:
                    is_authorized = await validate_scopes(request, scopes, user_scopes, require_all, require_all_actions, *args, **kwargs)
            else:
                is_authorized = False

            if is_authorized:
                # the user is authorized.
                # run the handler method and return the response
                response = await f(request, *args, **kwargs)
                return response
            else:
                # the user is not authorized.
                return json({
                    'status': 'not_authorized',
                }, 403)
            return response
        return decorated_function
    return decorator
