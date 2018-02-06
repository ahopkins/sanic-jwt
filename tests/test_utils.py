import pytest
from sanic_jwt import utils


@pytest.mark.asyncio
async def test_call_maybe_coro():
    def sync_func(a, b, c=0):
        return a + b + c

    async def async_func(a=1, b=2, c=0):
        return a + b + c

    assert await utils.call_maybe_coro(None) is None
    assert await utils.call_maybe_coro(1) == 1
    assert await utils.call_maybe_coro('hello') == 'hello'
    assert await utils.call_maybe_coro(sync_func, 1, 1) == 2
    assert await utils.call_maybe_coro(sync_func, a=0, b=2, c=1) == 3
    assert await utils.call_maybe_coro(sync_func, 1, 2, 3) == 6
    assert await utils.call_maybe_coro(async_func, 1, 1) == 2
    assert await utils.call_maybe_coro(async_func, a=0, b=2, c=1) == 3
    assert await utils.call_maybe_coro(async_func, 1, 2, 3) == 6
    assert await utils.call_maybe_coro(async_func) == 3
