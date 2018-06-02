import asyncio

from .exceptions import LoopNotRunning


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
        asyncio.Task.current_task(loop=loop)._sanicjwt = {}
    except AttributeError:  # noqa
        pass
