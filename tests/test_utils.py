import pytest
from sanic_jwt import utils
from sanic_jwt import exceptions
from pathlib import Path
from os import path


@pytest.fixture
def fcontent():
    return "3b$FGj@);[{~&+Lx>adYR+iG_QqGC3EI7FsbQAV@Nj&m&&mT\n"


@pytest.mark.asyncio
async def test_call():

    def sync_func(a, b, c=0):
        return a + b + c

    async def async_func(a=1, b=2, c=0):
        return a + b + c

    assert await utils.call(None) is None
    assert await utils.call(1) == 1
    assert await utils.call("hello") == "hello"
    assert await utils.call(sync_func, 1, 1) == 2
    assert await utils.call(sync_func, a=0, b=2, c=1) == 3
    assert await utils.call(sync_func, 1, 2, 3) == 6
    assert await utils.call(async_func, 1, 1) == 2
    assert await utils.call(async_func, a=0, b=2, c=1) == 3
    assert await utils.call(async_func, 1, 2, 3) == 6
    assert await utils.call(async_func) == 3


def test_load_file_or_str_with_Path(fcontent):
    p = Path(__file__).parent / "resources" / "test-file.txt"
    assert utils.load_file_or_str(str(p)) == fcontent
    assert utils.load_file_or_str(p) == fcontent
    assert utils.load_file_or_str(fcontent) == fcontent

    with pytest.raises(exceptions.ProvidedPathNotFound):
        utils.load_file_or_str(Path(__file__) / "foobar")


def test_load_file_or_str_with_str(fcontent):
    p = path.join(
        path.dirname(str(path.abspath(__file__))), "resources", "test-file.txt"
    )
    assert utils.load_file_or_str(p) == fcontent
