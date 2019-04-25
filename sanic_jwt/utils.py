import binascii
import datetime
import inspect
import logging
import os
from pathlib import Path

from . import exceptions

logger = logging.getLogger(__name__)


def generate_token(n=24, *args, **kwargs):
    return str(binascii.hexlify(os.urandom(n)), "utf-8")


def build_claim_iss(attr, *args, **kwargs):
    return attr


def build_claim_iat(attr, *args, **kwargs):
    return datetime.datetime.utcnow() if attr else None


def build_claim_nbf(attr, config, *args, **kwargs):
    seconds = config.leeway() + config.claim_nbf_delta()
    return (
        datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)
        if attr
        else None
    )


def build_claim_aud(attr, *args, **kwargs):
    return attr


async def call(fn, *args, **kwargs):
    if inspect.iscoroutinefunction(fn) or inspect.isawaitable(fn):
        fn = await fn(*args, **kwargs)
    elif callable(fn):
        fn = fn(*args, **kwargs)
    return fn


def load_file_or_str(path_or_str):
    if isinstance(path_or_str, Path):
        if os.path.isfile(str(path_or_str)):
            logger.debug('reading file "{}"'.format(str(path_or_str)))
            return path_or_str.read_text()

        else:
            raise exceptions.ProvidedPathNotFound

    elif isinstance(path_or_str, str):  # noqa
        if os.path.isfile(path_or_str):
            return Path(path_or_str).read_text()

    return path_or_str


def algorithm_is_asymmetric(algorithm):
    """This is a simple method to verify the need to provide a private key to
    a given ``algorithm``, as `documented by PyJWT
    <https://pyjwt.readthedocs.io/en/latest/algorithms.html>`_

    :param algorithm: the given algorithm, like HS256, ES384, RS512, PS256, etc
    :return: True if algorithm is asymmetric
    """
    return algorithm.lower()[:2] in ("rs", "es", "ps")
