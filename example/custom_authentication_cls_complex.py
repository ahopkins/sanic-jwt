import random
from datetime import datetime

from sanic import Sanic
from sanic.response import json

from sanic_jwt import (
    Authentication,
    Claim,
    Configuration,
    exceptions,
    Initialize,
    Responses,
)


class User:
    def __init__(self, _id, username):
        self.user_id = _id
        self.username = username
        self._permakey = None
        self._last_login = None

    def __repr__(self):
        return "User(id='{}')".format(self.user_id)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "last_login": self.last_login,
        }

    @property
    def permakey(self):
        return self._permakey

    @permakey.setter
    def permakey(self, value):
        self._permakey = value

    @property
    def last_login(self):
        return self._last_login

    @last_login.setter
    def last_login(self, value):
        self._last_login = value


USERS = []
username_table = {u.username: u for u in USERS}
userid_table = {u.user_id: u for u in USERS}


class MyConfig(Configuration):
    def get_verify_exp(self, request):
        """
        If the request is with the "permakey", then we do not want to check for expiration
        """
        return not "permakey" in request.headers


class MyAuthentication(Authentication):
    async def _verify(
        self,
        request,
        return_payload=False,
        verify=True,
        raise_missing=False,
        request_args=None,
        request_kwargs=None,
        *args,
        **kwargs
    ):
        """
        If there is a "permakey", then we will verify the token by checking the
        database. Otherwise, just do the normal verification.

        Typically, any method that begins with an underscore in sanic-jwt should
        not be touched. In this case, we are trying to break the rules a bit to handle
        a unique use case: handle both expirable and non-expirable tokens.
        """

        if "permakey" in request.headers:
            # Extract the permakey from the headers
            permakey = request.headers.get("permakey")

            # In production, probably should have some exception handling Here
            # in case the permakey is an empty string or some other bad value
            payload = await self._decode(permakey, verify=verify)

            # Sometimes, the application will call _verify(...return_payload=True)
            # So, let's make sure to handle this scenario.
            if return_payload:
                return payload

            # Retrieve the user from the database
            user_id = payload.get("user_id", None)
            user = userid_table.get(user_id)

            # If we cannot find a user, then this method should return
            # is_valid == False
            # reason == some text for why
            # status == some status code, probably a 401
            if not user_id or not user:
                is_valid = False
                reason = "No user found"
                status = 401
            else:
                # After finding a user, make sure the permakey matches,
                # or else return a bad status or some other error.
                # In production, both this scenario, and the above "No user found"
                # scenario should return an identical message and status code.
                # This is to prevent your application accidentally
                # leaking information about the existence or non-existence of users.
                is_valid = user.permakey == permakey
                reason = None if is_valid else "Permakey mismatch"
                status = 200 if is_valid else 401

            return is_valid, status, reason
        else:
            return await super()._verify(
                request=request,
                return_payload=return_payload,
                verify=verify,
                raise_missing=raise_missing,
                request_args=request_args,
                request_kwargs=request_kwargs,
                *args,
                **kwargs
            )

    async def authenticate(self, request, *args, **kwargs):
        username = request.json.get("username", None)
        password = request.json.get("password", None)

        if not username or not password:
            raise exceptions.AuthenticationFailed(
                "Missing username or password."
            )

        # Here, you would want to try to verify the username and password.
        # In this example, we are simply creating a new user if it does not
        # exist, and then authenticating the new user.
        user = username_table.get(username)
        if not user:
            user = User(len(USERS) + 1, username)
            USERS.append(user)
            username_table.update({user.username: user})
            userid_table.update({user.user_id: user})

            user.permakey = await self.generate_access_token(user)

        user.last_login = datetime.utcnow().strftime("%c")

        return user

    async def retrieve_user(self, request, payload, *args, **kwargs):
        if payload:
            user_id = payload.get("user_id", None)
            return userid_table.get(user_id)

        else:
            return None


def my_payload_extender(payload, *args, **kwargs):
    user_id = payload.get("user_id", None)
    user = userid_table.get(user_id)
    payload.update({"username": user.username})

    return payload


class MyResponses(Responses):
    @staticmethod
    def extend_authenticate(
        request, user=None, access_token=None, refresh_token=None
    ):
        return {"permakey": user.permakey}


class RandomClaim(Claim):
    """
    This custom claim is not necessary. It is merely being added so that everytime
    that await Authentication.generate_access_token() is being called, it will
    provide a different token. It is for illustrative purposes only
    """

    key = "rand"

    def setup(self, *args, **kwargs):
        return random.random()

    def verify(self, *args, **kwargs):
        return True


# elsewhere in the universe ...
if __name__ == "__main__":
    app = Sanic(__name__)

    sanicjwt = Initialize(
        app,
        authentication_class=MyAuthentication,
        configuration_class=MyConfig,
        # Following settings are for example purposes only
        responses_class=MyResponses,
        custom_claims=[RandomClaim],
        extend_payload=my_payload_extender,
        expiration_delta=15,
        leeway=0,
    )

    @app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @app.route("/protected")
    @sanicjwt.protected()
    async def protected_request(request):
        return json({"protected": True})

    # this route is for demonstration only

    @app.route("/cache")
    @sanicjwt.protected()
    async def protected_cache(request):
        print(USERS)
        return json(userid_table)

    app.run(debug=True, port=8888)
