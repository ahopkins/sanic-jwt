from sanic import Blueprint, Sanic
from sanic.response import json, text

import pytest
from sanic_jwt import Claim, exceptions, Initialize
from sanic_jwt.decorators import protected


class User:
    def __init__(self, id, username, password):
        self.user_id = id
        self.username = username
        self.password = password

    def to_dict(self):
        properties = ["user_id", "username"]
        return {prop: getattr(self, prop, None) for prop in properties}


@pytest.yield_fixture
def users():
    yield [User(1, "user1", "abcxyz"), User(2, "user2", "abcxyz")]


@pytest.yield_fixture
def username_table(users):
    yield {u.username: u for u in users}


@pytest.yield_fixture
def userid_table(users):
    yield {u.user_id: u for u in users}


@pytest.yield_fixture
def authenticate(username_table):
    async def authenticate(request, *args, **kwargs):
        username = request.json.get("username", None)
        password = request.json.get("password", None)

        if not username or not password:
            raise exceptions.AuthenticationFailed(
                "Missing username or password."
            )

        user = username_table.get(username, None)
        if user is None:
            raise exceptions.AuthenticationFailed("User not found.")

        if password != user.password:
            raise exceptions.AuthenticationFailed("Password is incorrect.")

        return user

    yield authenticate


@pytest.yield_fixture
def retrieve_user(userid_table):
    async def retrieve_user(request, payload, *args, **kwargs):
        if payload:
            user_id = payload.get("user_id", None)
            if user_id is not None:
                return userid_table.get(user_id)

        else:
            return None

    yield retrieve_user


@pytest.yield_fixture
def app(username_table, authenticate):

    sanic_app = Sanic()
    sanic_jwt = Initialize(sanic_app, authenticate=authenticate)

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    @sanic_app.route("/options", methods=["OPTIONS"])
    @protected()
    async def protected_request_options(request):
        return text("", status=204)

    @sanic_app.route("/protected/<verify:int>")
    @protected()
    def protected_regression_verify(request, verify):
        """
        for regression test see
        https://github.com/ahopkins/sanic-jwt/issues/59#issuecomment-380034269
        """
        return json({"protected": True})

    yield (sanic_app, sanic_jwt)


@pytest.yield_fixture
def app_with_refresh_token(username_table, authenticate):

    sanic_app = Sanic()
    sanic_jwt = Initialize(
        sanic_app,
        authenticate=authenticate,
        refresh_token_enabled=True,
        store_refresh_token=lambda user_id, refresh_token, request: True,
        retrieve_refresh_token=lambda user_id, request: True,
    )

    yield (sanic_app, sanic_jwt)


@pytest.yield_fixture
def app_with_url_prefix(username_table, authenticate):

    sanic_app = Sanic()
    sanic_jwt = Initialize(
        sanic_app, authenticate=authenticate, url_prefix="/somethingelse"
    )

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    yield (sanic_app, sanic_jwt)


@pytest.yield_fixture
def app_with_bp_setup_without_init(username_table, authenticate):
    sanic_app = Sanic()

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    sanic_bp = Blueprint("bp", url_prefix="/bp")

    @sanic_bp.route("/")
    async def bp_helloworld(request):
        return json({"hello": "world"})

    @sanic_bp.route("/protected")
    @protected()
    async def bp_protected_request(request):
        return json({"protected": True})

    yield (sanic_app, sanic_bp)


@pytest.yield_fixture
def app_with_bp(app_with_bp_setup_without_init):
    sanic_app, sanic_bp = app_with_bp_setup_without_init
    sanic_jwt_init = Initialize(sanic_app, authenticate=authenticate)
    sanic_jwt_init_bp = Initialize(
        sanic_bp, app=sanic_app, authenticate=authenticate
    )
    sanic_app.blueprint(sanic_bp)

    yield (sanic_app, sanic_jwt_init, sanic_bp, sanic_jwt_init_bp)


@pytest.yield_fixture
def app_with_extended_exp(username_table, authenticate):

    sanic_app = Sanic()
    sanic_jwt = Initialize(
        sanic_app, authenticate=authenticate, expiration_delta=(60 * 60)
    )

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    yield (sanic_app, sanic_jwt)


@pytest.yield_fixture
def app_with_leeway(username_table, authenticate):

    sanic_app = Sanic()
    sanic_jwt = Initialize(
        sanic_app, authenticate=authenticate, leeway=(60 * 5)
    )

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    yield (sanic_app, sanic_jwt)


@pytest.yield_fixture
def app_with_nbf(username_table, authenticate):

    sanic_app = Sanic()
    sanic_jwt = Initialize(
        sanic_app,
        authenticate=authenticate,
        claim_nbf=True,
        claim_nbf_delta=(60 * 5),
    )

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    yield (sanic_app, sanic_jwt)


@pytest.yield_fixture
def app_with_iat(username_table, authenticate):

    sanic_app = Sanic()
    sanic_jwt = Initialize(
        sanic_app, authenticate=authenticate, claim_iat=True
    )

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    yield (sanic_app, sanic_jwt)


@pytest.yield_fixture
def app_with_iss(username_table, authenticate):

    sanic_app = Sanic()
    sanic_jwt = Initialize(
        sanic_app, authenticate=authenticate, claim_iss="issuingserver"
    )

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    yield (sanic_app, sanic_jwt)


@pytest.yield_fixture
def app_with_aud(username_table, authenticate):

    sanic_app = Sanic()
    sanic_jwt = Initialize(
        sanic_app, authenticate=authenticate, claim_aud="clientserver"
    )

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    yield (sanic_app, sanic_jwt)


@pytest.yield_fixture
def app_with_retrieve_user(retrieve_user, authenticate):

    sanic_app = Sanic()
    sanic_jwt = Initialize(
        sanic_app, authenticate=authenticate, retrieve_user=retrieve_user
    )

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    yield (sanic_app, sanic_jwt)


@pytest.yield_fixture
def app_with_extra_verification(authenticate):
    def user2(payload):
        return payload.get("user_id") == 2

    extra_verifications = [user2]

    sanic_app = Sanic()
    sanic_jwt = Initialize(
        sanic_app,
        authenticate=authenticate,
        extra_verifications=extra_verifications,
    )

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    yield (sanic_app, sanic_jwt)


@pytest.yield_fixture
def app_with_custom_claims(authenticate):
    class User2Claim(Claim):
        key = "username"

        def setup(self, payload, user):
            return user.username

        def verify(self, value):
            return value == "user2"

    custom_claims = [User2Claim]

    sanic_app = Sanic()
    sanic_jwt = Initialize(
        sanic_app, authenticate=authenticate, custom_claims=custom_claims
    )

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    yield (sanic_app, sanic_jwt)
