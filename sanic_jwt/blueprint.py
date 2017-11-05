from sanic.response import json, text
from sanic import Blueprint
from . import exceptions


bp = Blueprint('auth_bp')


async def get_access_token_output(request, user):
    access_token = await request.app.auth.get_access_token(user)

    output = {
        request.app.config.SANIC_JWT_ACCESS_TOKEN_NAME: access_token
    }

    return access_token, output


def get_token_reponse(request, access_token, output, refresh_token=None):
    response = json(output)

    if request.app.config.SANIC_JWT_COOKIE_SET:
        key = request.app.config.SANIC_JWT_COOKIE_TOKEN_NAME
        response.cookies[key] = str(access_token, 'utf-8')
        response.cookies[key]['domain'] = request.app.config.SANIC_JWT_COOKIE_DOMAIN
        response.cookies[key]['httponly'] = request.app.config.SANIC_JWT_COOKIE_HTTPONLY

        if refresh_token and request.app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED:
            key = request.app.config.SANIC_JWT_COOKIE_REFRESH_TOKEN_NAME
            response.cookies[key] = refresh_token
            response.cookies[key]['domain'] = request.app.config.SANIC_JWT_COOKIE_DOMAIN
            response.cookies[key]['httponly'] = request.app.config.SANIC_JWT_COOKIE_HTTPONLY

    return response


@bp.listener('before_server_start')
async def setup_claims(app, *args, **kwargs):
    app.auth.setup_claims()


@bp.route('/', methods=['POST', 'OPTIONS'])
async def authenticate(request, *args, **kwargs):
    if request.method == 'OPTIONS':
        return text('', status=204)
    try:
        user = await request.app.auth.authenticate(request, *args, **kwargs)
    except Exception as e:
        raise e

    access_token, output = await get_access_token_output(request, user)

    if request.app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED:
        refresh_token = request.app.auth.get_refresh_token(user)
        output.update({
            request.app.config.SANIC_JWT_REFRESH_TOKEN_NAME: refresh_token
        })
    else:
        refresh_token = None

    response = get_token_reponse(request, access_token, output, refresh_token)

    return response


@bp.get('/me')
async def retrieve_user(request, *args, **kwargs):
    if not hasattr(request.app.auth, 'retrieve_user'):
        raise exceptions.MeEndpointNotSetup()

    try:
        payload = request.app.auth.extract_payload(request)
        user = request.app.auth.retrieve_user(request, payload)
    except exceptions.MissingAuthorizationCookie:
        user = None
        payload = None
    if not user:
        me = None
    else:
        me = user.to_dict() if hasattr(user, 'to_dict') else dict(user)

    output = {
        'me': me
    }

    response = json(output)

    if payload is None and request.app.config.SANIC_JWT_COOKIE_SET:
        key = request.app.config.SANIC_JWT_COOKIE_TOKEN_NAME
        del response.cookies[key]

    return response


@bp.get('/verify')
async def verify(request, *args, **kwargs):
    is_valid, status, reason = request.app.auth.verify(request, *args, **kwargs)

    response = {
        'valid': is_valid
    }

    if reason:
        response.update({'reason': reason})

    return json(response, status=status)


@bp.route('/refresh', methods=['POST', 'OPTIONS'])
async def refresh(request, *args, **kwargs):
    if request.method == 'OPTIONS':
        return text('', status=204)
    # TODO:
    # - Add exceptions
    payload = request.app.auth.extract_payload(request, verify=False)
    user = request.app.auth.retrieve_user(request, payload=payload)
    user_id = request.app.auth._get_user_id(user)
    refresh_token = request.app.auth.retrieve_refresh_token(request=request, user_id=user_id)
    if isinstance(refresh_token, bytes):
        refresh_token = refresh_token.decode('utf-8')
    refresh_token = str(refresh_token)
    print('user_id: ', user_id)
    print('Retrieved token: ', refresh_token)
    purported_token = request.app.auth.retrieve_refresh_token_from_request(request)
    print('Purported token: ', purported_token)

    if refresh_token != purported_token:
        raise exceptions.AuthenticationFailed()

    access_token, output = get_access_token_output(request, user)
    response = get_token_reponse(request, access_token, output)

    return response
