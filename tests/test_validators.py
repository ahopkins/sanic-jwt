from sanic_jwt.validators import validate_single_scope


def test_validate_single_scope():
    assert validate_single_scope("user", ["something"]) is False
    assert validate_single_scope("user", ["user"])
    assert validate_single_scope("user:read", ["user"])
    assert validate_single_scope("user:read", ["user:read"])
    assert validate_single_scope("user:read", ["user:write"]) is False
    assert validate_single_scope("user:read", ["user:read:write"])
    assert validate_single_scope("user", ["user:read"]) is False
    assert validate_single_scope("user:read:write", ["user:read"]) is False
    assert validate_single_scope("user:read:write", ["user:read:write"])
    assert validate_single_scope("user:read:write", ["user:write:read"])
    assert validate_single_scope("user:read:write", ["user:read"], False)
    assert validate_single_scope("user", ["something", "else"]) is False
    assert validate_single_scope("user", ["something", "else", "user"])
    assert validate_single_scope("user:read", ["something:else", "user:read"])
    assert validate_single_scope("user:read", ["user:read", "something:else"])
    assert validate_single_scope(":read", [":read"])
    assert validate_single_scope(":read", ["admin"])
    assert validate_single_scope("user", []) is False
    assert validate_single_scope("user", [None]) is False
    assert validate_single_scope("user", [None, "user"])
