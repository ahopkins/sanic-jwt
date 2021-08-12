from sanic_jwt import exceptions


class Claim:
    def __init__(self):
        required = ("key", "setup", "verify")
        if any(not hasattr(self, x) for x in required):
            raise exceptions.InvalidCustomClaim()

    @classmethod
    def _register(cls, sanicjwt):
        instance = cls()
        sanicjwt.instance.ctx.auth._custom_claims.add(instance)

    def get_key(self):
        return self.key

    def _verify(self, payload):
        key = self.get_key()
        value = payload.get(key)
        valid_claim = self.verify(value)
        if not isinstance(valid_claim, bool):
            raise exceptions.InvalidCustomClaim()

        if valid_claim is False:
            message = "Invalid claim: {}".format(key)
            raise exceptions.InvalidCustomClaimError(message=message)
