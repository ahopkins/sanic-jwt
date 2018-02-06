from datetime import datetime, timedelta

from sanic_jwt import exceptions, utils


async def build_payload(authenticator, user, *args, **kwargs):
    if isinstance(user, dict):
        user_id = user.get(authenticator.app.config.SANIC_JWT_USER_ID)
    elif hasattr(user, 'to_dict'):
        _to_dict = await utils.call_maybe_coro(user.to_dict)
        user_id = _to_dict.get(authenticator.app.config.SANIC_JWT_USER_ID)
    else:
        raise exceptions.InvalidRetrieveUserObject()

    return {
        'user_id': user_id,
    }


async def extend_payload(authenticator, payload, *args, **kwargs):
    delta = timedelta(
        seconds=authenticator.app.config.SANIC_JWT_EXPIRATION_DELTA)
    exp = datetime.utcnow() + delta
    additional = {
        'exp': exp
    }

    for option in ['iss', 'iat', 'nbf', 'aud', ]:
        setting = 'SANIC_JWT_CLAIM_{}'.format(option.upper())
        attr = getattr(authenticator.app.config, setting, False)
        if attr:
            method_name = 'build_claim_{}'.format(option)
            method = getattr(utils, method_name)
            additional.update({option: method(attr, authenticator.app.config)})

    payload.update(additional)

    return payload
