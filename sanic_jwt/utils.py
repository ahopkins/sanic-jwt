import importlib
import binascii
import os
import datetime


def generate_token(n=24):
    return str(binascii.hexlify(os.urandom(n)), 'utf-8')


async def execute_handler(handler, *args, **kwargs):
    if isinstance(handler, str):
        parts = handler.split('.')
        fn = parts.pop()
        module = importlib.import_module('.'.join(parts))
        method = getattr(module, fn)
    else:
        method = handler
    runner = await method(*args, **kwargs)
    return runner


def build_claim_iss(attr, *args, **kwargs):
    return attr


def build_claim_iat(attr, *args, **kwargs):
    return datetime.datetime.utcnow() if attr else None


def build_claim_nbf(attr, config, *args, **kwargs):
    seconds = config.SANIC_JWT_LEEWAY + config.SANIC_JWT_CLAIM_NBF_DELTA
    return datetime.datetime.utcnow() + datetime.timedelta(
        seconds=seconds
    ) if attr else None


def build_claim_aud(attr, *args, **kwargs):
    return attr


def load_settings(app, settings):
    for setting in dir(settings):
        if setting.isupper() and setting not in app.config:
            value = getattr(settings, setting)
            setattr(app.config, setting, value)
