from functools import wraps
from sanic.response import json


def protected():
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
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
    return decorator
