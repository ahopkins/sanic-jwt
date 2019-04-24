from sanic_jwt import exceptions


class Claim:
    @classmethod
    def _register(cls, sanicjwt):
        required = ("key", "setup", "verify")
        instance = cls()
        if any(not hasattr(instance, x) for x in required):
            raise AttributeError

        sanicjwt.instance.auth._custom_claims.add(instance)

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
