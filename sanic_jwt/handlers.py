def build_payload(authenticator, user):
    if isinstance(user, dict):
        user_id = user.get(authenticator.app.config.SANIC_JWT_USER_ID)
    else:
        user_id = getattr(user, authenticator.app.config.SANIC_JWT_USER_ID)

    return {
        'user_id': user_id,
    }
