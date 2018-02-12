from sanic_jwt import utils


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


async def validate_scopes(
    request,
    scopes,
    user_scopes,
    require_all=True,
    require_all_actions=True,
    *args,
    **kwargs
):
    scopes = await utils.call(scopes, request, *args, **kwargs)

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
