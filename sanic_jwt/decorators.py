import logging
from contextlib import contextmanager
from copy import deepcopy
from functools import wraps
from inspect import isawaitable

from sanic import Blueprint
from sanic.response import redirect
from sanic.views import HTTPMethodView

from . import exceptions, utils
from .cache import clear_cache, to_cache
from .validators import validate_scopes

logger = logging.getLogger(__name__)


@contextmanager
def instant_config(instance, **kwargs):
    if kwargs and hasattr(instance, "auth"):
        to_cache("_request", kwargs.get("request"))
        for key, val in kwargs.items():
            if key in instance.auth.config:
                if callable(val):
                    val = val()
                to_cache(key, val)
    yield

    clear_cache()


async def _do_protection(*args, **kwargs):
    initialized_on = kwargs.pop("initialized_on")
    kw = kwargs.pop("kw")
    request = kwargs.pop("request")
    f = kwargs.pop("f")

    use_kwargs = deepcopy(kwargs)
    if "return_response" in use_kwargs:
        use_kwargs.pop("return_response")

    if initialized_on and isinstance(initialized_on, Blueprint):
        instance = initialized_on
    else:
        instance = request.app

    with instant_config(instance, request=request, **kw):
        if request.method == "OPTIONS":
            response = f(request, *args, **use_kwargs)
            if isawaitable(response):  # noqa
                response = await response
            if kwargs.get("return_response", True):
                return response

            else:
                return True, response

        try:
            if instance.auth.config.do_protection():
                (
                    is_authenticated,
                    status,
                    reasons,
                ) = instance.auth._check_authentication(
                    request, request_args=args, request_kwargs=use_kwargs
                )
            else:
                is_authenticated = True
                status = 200
                reasons = None
        except AttributeError:
            raise exceptions.SanicJWTException(
                "Authentication instance not found. Perhaps you used "
                "@protected without passing in a blueprint? "
                "Try @protected(blueprint)",
                status_code=500,
            )

        except exceptions.SanicJWTException as e:
            is_authenticated = False
            status = e.status_code
            reasons = (
                instance.auth._reasons
                if (instance.auth._reasons and instance.auth.config.debug())
                else e.args[0]
            )

        if is_authenticated:
            if kwargs.get("return_response", True):
                response = f(request, *args, **use_kwargs)
                if isawaitable(response):
                    response = await response
                return response

            else:
                return True, instance

        else:
            if kw.get("redirect_on_fail", False):
                where_to = kw.get(
                    "redirect_url", instance.auth.config.login_redirect_url()
                )
                if where_to is not None:
                    return redirect(where_to, status=302)

            raise exceptions.Unauthorized(reasons, status_code=status)


def protected(initialized_on=None, **kw):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            if issubclass(request.__class__, HTTPMethodView):
                request = args[0]
            kwargs.update(
                {
                    "initialized_on": initialized_on,
                    "kw": kw,
                    "request": request,
                    "f": f,
                }
            )
            return await _do_protection(*args, **kwargs)

        return decorated_function

    return decorator


def scoped(
    scopes,
    require_all=True,
    require_all_actions=True,
    initialized_on=None,
    **kw
):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            if issubclass(request.__class__, HTTPMethodView):
                request = args[0]

            if scopes is not None and scopes is not False:
                protect_kwargs = deepcopy(kwargs)
                protect_kwargs.update(
                    {
                        "initialized_on": initialized_on,
                        "kw": kw,
                        "request": request,
                        "f": f,
                        "return_response": False,
                    }
                )
                _, instance = await _do_protection(*args, **protect_kwargs)

                if request.method == "OPTIONS":
                    return instance

                user_scopes = instance.auth.extract_scopes(request)
                override = instance.auth.override_scope_validator
                destructure = instance.auth.destructure_scopes
                if user_scopes is None:
                    # If there are no defined scopes in the payload,
                    # deny access
                    is_authorized = False
                    status = 403
                    reasons = "Invalid scope."

                    # TODO:
                    # - add login_redirect_url
                    raise exceptions.Unauthorized(reasons, status_code=status)

                else:
                    is_authorized = await validate_scopes(
                        request,
                        scopes,
                        user_scopes,
                        require_all=require_all,
                        require_all_actions=require_all_actions,
                        override=override,
                        destructure=destructure,
                        request_args=args,
                        request_kwargs=kwargs,
                    )
                    if not is_authorized:
                        status = 403
                        reasons = "Invalid scope."

                        # TODO:
                        # - add login_redirect_url
                        raise exceptions.Unauthorized(
                            reasons, status_code=status
                        )

            # the user is authorized.
            # run the handler method and return the response
            # NOTE: it's possible to use return await.utils(f, ...) in
            # here, but inside the @protected decorator it wont work,
            # so this is left as is for now
            response = f(request, *args, **kwargs)
            if isawaitable(response):
                response = await response
            return response

        return decorated_function

    return decorator


def inject_user(initialized_on=None, **kw):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            if issubclass(request.__class__, HTTPMethodView):
                request = args[0]

            if initialized_on and isinstance(
                initialized_on, Blueprint
            ):  # noqa
                instance = initialized_on
            else:
                instance = request.app

            with instant_config(instance, request=request, **kw):
                if request.method == "OPTIONS":
                    return await utils.call(
                        f, request, *args, **kwargs
                    )  # noqa

                payload = instance.auth.extract_payload(request, verify=False)
                user = await utils.call(
                    instance.auth.retrieve_user, request, payload
                )
                response = f(request, user=user, *args, **kwargs)
                return await response

        return decorated_function

    return decorator
