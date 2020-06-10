import asyncio
import math

from sanic import Sanic

from sanic_jwt import Claim, exceptions, Initialize


def is_prime(n):
    if n % 2 == 0 and n > 2:
        return False
    return all(n % i for i in range(3, int(math.sqrt(n)) + 1, 2))


app = Sanic()
sanicjwt = Initialize(app, auth_mode=False)

user7 = {"user_id": 7}
user8 = {"user_id": 8}


class UserIsPrime(Claim):
    key = "user_id_checker"

    def setup(self, payload, user):
        return user.get("user_id")

    def verify(self, value):
        return is_prime(value)


async def run():
    token = await app.auth.generate_access_token(
        user7, custom_claims=[UserIsPrime]
    )

    payload = await app.auth.verify_token(token, return_payload=True)
    try:
        is_verified = await app.auth.verify_token(
            token, custom_claims=[UserIsPrime]
        )
    except exceptions.InvalidCustomClaimError:
        is_verified = False
    finally:
        print("\n <User:7> | Passing")
        print("\t Payload:", payload)
        print("\t Is verified:", is_verified)

    token = await app.auth.generate_access_token(
        user8, custom_claims=[UserIsPrime]
    )

    payload = await app.auth.verify_token(token, return_payload=True)
    try:
        is_verified = await app.auth.verify_token(
            token, custom_claims=[UserIsPrime]
        )
    except exceptions.InvalidCustomClaimError:
        is_verified = False
    finally:
        print("\n <User:8> | Failing")
        print("\t Payload:", payload)
        print("\t Is verified:", is_verified)


asyncio.run(run())
