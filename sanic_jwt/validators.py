def validate_single_scope(required, user_scopes, require_all_actions=True):
    def normalize(scope):
        """
        Normalizes and returns tuple consisting of namespace, and action(s)
        """
        parts = scope.split(':')
        return (parts[0], parts[1:])

    required = normalize(required)
    user_scopes = [normalize(x) for x in user_scopes]

    is_valid = False

    for requested in user_scopes:
        if required[0]:
            valid_namespace = required[0] == requested[0]
        else:
            valid_namespace = True

        if required[1]:
            if len(requested[1]) == 0:
                valid_actions = True
            else:
                method = all if require_all_actions else any
                valid_actions = method(x in requested[1] for x in required[1])
        else:
            valid_actions = len(requested[1]) == 0

        is_valid = all([valid_namespace, valid_actions])

        if is_valid:
            break

    return is_valid


def validate_scopes(request, scopes, user_scopes, require_all=True, require_all_actions=True):
    if not isinstance(scopes, (list, tuple)):
        scopes = [scopes]

    method = all if require_all else any
    return method(
        validate_single_scope(
            x,
            user_scopes,
            require_all_actions=require_all_actions
        ) for x in scopes
    )


# print(1, 'False', validate_single_scope('user', ['something']))
# print(2, 'True', validate_single_scope('user', ['user']))
# print(3, 'True', validate_single_scope('user:read', ['user']))
# print(4, 'True', validate_single_scope('user:read', ['user:read']))
# print(5, 'False', validate_single_scope('user:read', ['user:write']))
# print(6, 'True', validate_single_scope('user:read', ['user:read:write']))
# print(7, 'False', validate_single_scope('user', ['user:read']))
# print(8, 'False', validate_single_scope('user:read:write', ['user:read']))
# print(9, 'True', validate_single_scope('user:read:write', ['user:read:write']))
# print(10, 'True', validate_single_scope('user:read:write', ['user:write:read']))
# print(11, 'True', validate_single_scope('user:read:write', ['user:read'], False))


# print(12, 'False', validate_single_scope('user', ['something', 'else']))
# print(13, 'True', validate_single_scope('user', ['something', 'else', 'user']))
# print(14, 'True', validate_single_scope('user:read', ['something:else', 'user:read']))
# print(15, 'True', validate_single_scope('user:read', ['user:read', 'something:else']))

# print(16, 'True', validate_single_scope(':read', [':read']))
# print(17, 'True', validate_single_scope(':read', ['admin']))
