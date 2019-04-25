import pytest
from sanic_jwt import exceptions
from sanic_jwt.cache import is_cached


def test_cache_is_not_running():
    with pytest.raises(exceptions.LoopNotRunning):
        assert is_cached("_request") is not None
