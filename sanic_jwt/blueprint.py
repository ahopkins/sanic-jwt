from sanic.response import json
from sanic import Blueprint


bp = Blueprint('auth_bp')


@bp.post('/')
async def authenticate(request, *args, **kwargs):
    try:
        user = request.app.auth.authenticate(request, *args, **kwargs)
    except Exception as e:
        raise e


    return json({
        'access_token': request.app.auth.get_access_token(user)
    })

@bp.get('/verify')
async def verify(request, *args, **kwargs):
    is_valid, status, reason = request.app.auth.verify(request, *args, **kwargs)

    response = {
        'valid': is_valid
    }

    if reason:
        response.update({'reason': reason})

    return json(response, status=status)
