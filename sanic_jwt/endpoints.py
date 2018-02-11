from . import exceptions
from . import utils
# from .response import get_access_token_output
# from .response import get_token_reponse
from sanic.response import json
from sanic.response import text


response = None


# @bp.listener('before_server_start')
async def setup_claims(app, *args, **kwargs):
    app.auth.setup_claims()


# @bp.route('/', methods=['POST', 'OPTIONS'], strict_slashes=False)
async def authenticate(request, *args, **kwargs):
    if request.method == 'OPTIONS':
        return text('', status=204)
    user = await utils.call(
        request.app.auth.authenticate, request, *args, **kwargs)
    # except Exception as e:
    #     raise e

    access_token, output = await response.get_access_token_output(request, user)

    if request.app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED:
        refresh_token = await utils.call(
            request.app.auth.get_refresh_token, request, user)
        output.update({
            request.app.config.SANIC_JWT_REFRESH_TOKEN_NAME: refresh_token
        })
    else:
        refresh_token = None

    resp = response.get_token_reponse(request, access_token, output, refresh_token)

    return resp


# @bp.get('/me')
async def retrieve_user(request, *args, **kwargs):
    if not hasattr(request.app.auth, 'retrieve_user'):
        raise exceptions.MeEndpointNotSetup()

    try:
        payload = request.app.auth.extract_payload(request)
        user = await utils.call(
            request.app.auth.retrieve_user, request, payload)
    except exceptions.MissingAuthorizationCookie:
        user = None
        payload = None

    if not user:
        me = None
    else:
        if hasattr(user, 'to_dict'):
            me = await utils.call(user.to_dict)
        else:
            me = dict(user)

    output = {
        'me': me
    }

    response = json(output)

    if payload is None and request.app.config.SANIC_JWT_COOKIE_SET:
        key = request.app.config.SANIC_JWT_COOKIE_ACCESS_TOKEN_NAME
        del response.cookies[key]

    return response


# @bp.route('/verify', methods=['GET', 'OPTIONS'])
async def verify(request, *args, **kwargs):
    if request.method == 'OPTIONS':
        return text('', status=204)
    is_valid, status, reason = request.app.auth.verify(
        request, *args, **kwargs)

    response = {
        'valid': is_valid
    }

    if reason:
        response.update({'reason': reason})

    return json(response, status=status)


# @bp.route('/refresh', methods=['POST', 'OPTIONS'])
async def refresh(request, *args, **kwargs):
    if request.method == 'OPTIONS':
        return text('', status=204)
    # TODO:
    # - Add exceptions
    payload = request.app.auth.extract_payload(request, verify=False)
    user = await utils.call(
        request.app.auth.retrieve_user, request, payload=payload)
    user_id = await request.app.auth._get_user_id(user)
    refresh_token = await utils.call(
        request.app.auth.retrieve_refresh_token,
        request=request,
        user_id=user_id)
    if isinstance(refresh_token, bytes):
        refresh_token = refresh_token.decode('utf-8')
    refresh_token = str(refresh_token)
    purported_token = await request.app.auth\
        .retrieve_refresh_token_from_request(request)

    if refresh_token != purported_token:
        raise exceptions.AuthenticationFailed()

    access_token, output = await response.get_access_token_output(request, user)
    resp = response.get_token_reponse(request, access_token, output)

    return resp
