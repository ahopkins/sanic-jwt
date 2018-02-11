from sanic.response import json


async def get_access_token_output(request, user):
    access_token = await request.app.auth.get_access_token(user)

    output = {request.app.config.SANIC_JWT_ACCESS_TOKEN_NAME: access_token}

    return access_token, output


def get_token_reponse(request, access_token, output, refresh_token=None):
    response = json(output)

    if request.app.config.SANIC_JWT_COOKIE_SET:
        key = request.app.config.SANIC_JWT_COOKIE_ACCESS_TOKEN_NAME
        response.cookies[key] = str(access_token, 'utf-8')
        response.cookies[key]['domain'] = \
            request.app.config.SANIC_JWT_COOKIE_DOMAIN
        response.cookies[key]['httponly'] = \
            request.app.config.SANIC_JWT_COOKIE_HTTPONLY

        if refresh_token and \
                request.app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED:
            key = request.app.config.SANIC_JWT_COOKIE_REFRESH_TOKEN_NAME
            response.cookies[key] = refresh_token
            response.cookies[key]['domain'] = \
                request.app.config.SANIC_JWT_COOKIE_DOMAIN
            response.cookies[key]['httponly'] = \
                request.app.config.SANIC_JWT_COOKIE_HTTPONLY

    return response
