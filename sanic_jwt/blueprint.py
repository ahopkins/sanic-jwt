from sanic.response import json, text
from sanic import Blueprint


bp = Blueprint('auth_bp')


@bp.route('/', methods=['POST', 'OPTIONS'])
async def authenticate(request, *args, **kwargs):
    if request.method == 'OPTIONS':
        return text('', status=204)
    try:
        user = request.app.auth.authenticate(request, *args, **kwargs)
    except Exception as e:
        raise e

    access_token = request.app.auth.get_access_token(user)

    output = {
        request.app.config.SANIC_JWT_ACCESS_TOKEN_NAME: access_token
    }

    if request.app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED:
        refresh_token = request.app.auth.get_refresh_token(user)
        output.update({
            request.app.config.SANIC_JWT_REFRESH_TOKEN_NAME: refresh_token
        })

    response = json(output)

    if request.app.config.SANIC_JWT_COOKIE_SET:
        key = request.app.config.SANIC_JWT_COOKIE_TOKEN_NAME
        response.cookies[key] = str(access_token, 'utf-8')
        response.cookies[key]['domain'] = request.app.config.SANIC_JWT_COOKIE_DOMAIN
        response.cookies[key]['httponly'] = request.app.config.SANIC_JWT_COOKIE_HTTPONLY

    return response


@bp.get('/me')
async def retrieve_user(request, *args, **kwargs):
    assert hasattr(request.app.auth, 'retrieve_user'),\
        "/me endpoint has not been setup. Pass retrieve_user if you with to proceeed."

    payload = request.app.auth.extract_payload(request)
    user = request.app.auth.retrieve_user(request, payload)
    if not user:
        me = None
    else:
        me = user.to_dict() if hasattr(user, 'to_dict') else dict(user)

    response = {
        'me': me
    }
    return json(response)


@bp.get('/verify')
async def verify(request, *args, **kwargs):
    is_valid, status, reason = request.app.auth.verify(request, *args, **kwargs)

    response = {
        'valid': is_valid
    }

    if reason:
        response.update({'reason': reason})

    return json(response, status=status)


@bp.post('/refresh')
async def refresh(request, *args, **kwargs):
    # TODO:
    # - Add exceptions
    refresh_token = request.app.auth.retrieve_refresh_token(request)
    user = request.app.auth.retrieve_user(request)

    response = {
        request.app.config.SANIC_JWT_ACCESS_TOKEN_NAME: request.app.auth.get_access_token(user)
    }
    return json(response)
