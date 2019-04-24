from sanic_jwt import utils


def normalize(scope):
    """
    Normalizes and returns tuple consisting of namespace, and action(s)
    """
    parts = scope.split(":")
    return (parts[0], parts[1:])


def validate_single_scope(
    required, user_scopes, require_all_actions=True, override=None
):

    if not user_scopes:
        return False

    elif user_scopes.count(None) > 0:
        if user_scopes.count(None) == len(user_scopes):
            return False

        user_scopes = list(filter(lambda v: v is not None, user_scopes))

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

    outcome = (
        override(is_valid, required, user_scopes, require_all_actions)
        if callable(override)
        else is_valid
    )
    return outcome


async def validate_scopes(
    request,
    scopes,
    user_scopes,
    override,
    destructure,
    require_all=True,
    require_all_actions=True,
    request_args=[],
    request_kwargs={},
):
    scopes = await utils.call(destructure, scopes)
    scopes = await utils.call(scopes, request, *request_args, **request_kwargs)

    if not isinstance(scopes, (list, tuple)):
        scopes = [scopes]

    method = all if require_all else any
    return method(
        validate_single_scope(
            x,
            user_scopes,
            require_all_actions=require_all_actions,
            override=override,
        )
        for x in scopes
    )
