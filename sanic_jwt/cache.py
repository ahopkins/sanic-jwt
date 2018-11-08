import asyncio
import sys

from .exceptions import LoopNotRunning


def _get_current_task(loop):  # noqa
    if sys.version_info[:2] < (3, 7):  # to avoid deprecation warning
        return asyncio.Task.current_task(loop=loop)

    else:
        return asyncio.current_task(loop=loop)


def _check_event_loop():
    if not asyncio.get_event_loop().is_running():
        raise LoopNotRunning


def _get_or_create_cache():
    loop = asyncio.get_event_loop()
    try:
        return _get_current_task(loop)._sanicjwt

    except AttributeError:
        _get_current_task(loop)._sanicjwt = {}
        return _get_current_task(loop)._sanicjwt


def get_cached(value):
    _check_event_loop()
    return _get_or_create_cache().get(value, None)


def is_cached(value):
    _check_event_loop()
    return value in _get_or_create_cache()


def to_cache(key, value):
    _check_event_loop()
    _get_or_create_cache().update({key: value})


def clear_cache():
    _check_event_loop()
    loop = asyncio.get_event_loop()
    try:
        _get_current_task(loop)._sanicjwt = {}
    except AttributeError:  # noqa
        pass
