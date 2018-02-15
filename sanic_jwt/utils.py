import binascii
import datetime
import importlib
import inspect
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


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
    seconds = config.leeway + config.claim_nbf_delta
    return datetime.datetime.utcnow() + datetime.timedelta(
        seconds=seconds
    ) if attr else None


def build_claim_aud(attr, *args, **kwargs):
    return attr


# To be depracated
def load_settings(app, settings):
    for setting in dir(settings):
        if setting.isupper() and setting not in app.config:
            value = getattr(settings, setting)
            setattr(app.config, setting, value)


async def call(fn, *args, **kwargs):
    if inspect.iscoroutinefunction(fn):
        fn = await fn(*args, **kwargs)
    elif callable(fn):
        fn = fn(*args, **kwargs)
    return fn


def load_file_or_str(path_or_str):
    if isinstance(path_or_str, Path) and \
            path_or_str.is_file():
        logger.debug('reading {}'.format(str(path_or_str)))
        return path_or_str.read_text()
    elif isinstance(path_or_str, str):
        p = Path(path_or_str)
        if p.is_file():
            return p.read_text()
        else:
            return path_or_str
    return path_or_str


def algorithm_is_asymmetric(algorithm):
    """This is a simple method to verify the need to provide a private key to
    a given ``algorithm``, as `documented by PyJWT
    <https://pyjwt.readthedocs.io/en/latest/algorithms.html>`_

    :param algorithm: the given algorithm, like HS256, ES384, RS512, PS256, etc
    :return: True is algorithm is asymmetric
    """
    return algorithm.lower()[:2] in ('rs', 'es', 'ps')
