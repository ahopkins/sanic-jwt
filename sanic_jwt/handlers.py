from datetime import datetime, timedelta


def build_payload(authenticator, user):
    user_id = getattr(user, authenticator.app.config.SANIC_JWT_USER_ID)
    delta = timedelta(seconds=authenticator.app.config.SANIC_JWT_EXPIRATION_DELTA)
    exp = datetime.utcnow() + delta

    return {
        'user_id': user_id,
        'exp': exp,
    }