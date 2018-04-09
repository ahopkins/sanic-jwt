import asyncio
# from collections import namedtuple

from .exceptions import LoopNotRunning


# CacheResult = namedtuple(
#     "CacheResult", ["fn_name", "ctx_id", "result"]
# )

def _check_event_loop():
    if not asyncio.get_event_loop().is_running():
        raise LoopNotRunning


def _get_or_create_cache():
    loop = asyncio.get_event_loop()
    try:
        return asyncio.Task.current_task(loop=loop)._sanicjwt
    except AttributeError:
        asyncio.Task.current_task(loop=loop)._sanicjwt = {}
        return asyncio.Task.current_task(loop=loop)._sanicjwt


def get_value(value):
    _check_event_loop()
    return _get_or_create_cache().get(value, None)


def has_value(value):
    _check_event_loop()
    return value in _get_or_create_cache()


def set_value(key, value):
    _check_event_loop()
    _get_or_create_cache().update({key: value})


def clear_value(key):
    _check_event_loop()
    if key in _get_or_create_cache():
        _get_or_create_cache().pop(key)
