import pytest
from sanic import Sanic
from sanic.response import json

from sanic_jwt import exceptions, Initialize
from sanic_jwt.decorators import protected, scoped


class User(object):

    def __init__(self, id, username, password, scopes):
        self.id = id
        self.username = username
        self.password = password
        self.scopes = scopes

    def to_dict(self):
        return {
            "user_id": self.id,
            "username": self.username,
            "scopes": self.scopes,
        }

    @property
    def user_id(self):
        raise Exception("you shall not call me")


@pytest.yield_fixture
def app_with_scopes():
    users = [
        User(1, "user1", "abcxyz", ["user"]),
        User(2, "user2", "abcxyz", ["user", "admin"]),
        User(3, "user3", "abcxyz", ["user:read"]),
        User(4, "user4", "abcxyz", ["client1"]),
        User(5, "user5", "abcxyz", ["admin"]),
        User(6, "user6", "abcxyz", None),
    ]

    username_table = {u.username: u for u in users}
    userid_table = {u.id: u for u in users}

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

    async def retrieve_user(request, payload, *args, **kwargs):
        if payload:
            user_id = payload.get("user_id", None)
            if user_id is not None:
                return userid_table.get(user_id)

        else:
            return None

    async def my_scope_extender(user, *args, **kwargs):
        return user.scopes

    sanic_app = Sanic()
    sanicjwt = Initialize(
        sanic_app,
        authenticate=authenticate,
        retrieve_user=retrieve_user,
        add_scopes_to_payload=my_scope_extender,
    )

    @sanic_app.route("/")
    async def test(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_route(request):
        return json({"protected": True, "scoped": False})

    @sanic_app.route("/protected/scoped/1")
    @protected()
    @scoped("user")
    async def protected_route1(request):
        return json({"protected": True, "scoped": True})

    @sanic_app.route("/protected/scoped/2")
    @protected()
    @scoped("user:read")
    async def protected_route2(request):
        return json({"protected": True, "scoped": True})

    @sanic_app.route("/protected/scoped/3")
    @protected()
    @scoped(["user", "admin"])
    async def protected_route3(request):
        return json({"protected": True, "scoped": True})

    @sanic_app.route("/protected/scoped/4")
    @protected()
    @scoped(["user", "admin"], False)
    async def protected_route4(request):
        return json({"protected": True, "scoped": True})

    @sanic_app.route("/protected/scoped/5")
    @scoped("user")
    async def protected_route5(request):
        return json({"protected": True, "scoped": True})

    @sanic_app.route("/protected/scoped/6/<id>")
    @scoped(lambda *args, **kwargs: "user")
    async def protected_route6(request, id):
        return json({"protected": True, "scoped": True, "id": id})

    def client_id_scope(request, *args, **kwargs):
        return "client" + kwargs.get("id")

    @sanic_app.route("/protected/scoped/7/<id>")
    @scoped(client_id_scope)
    async def protected_route7(request, id):
        return json({"protected": True, "scoped": True, "id": id})

    @sanic_app.route("/protected/scoped/8")
    @protected()
    @scoped(["user:read", "admin"], False)
    async def protected_route8(request):
        return json({"protected": True, "scoped": True})

    async def client_id_async_scope(request, *args, **kwargs):
        return "client" + kwargs.get("id")

    @sanic_app.route("/protected/scoped/9/<id>")
    @scoped(client_id_async_scope)
    async def protected_route9(request, id):
        return json({"protected": True, "scoped": True, "id": id})

    yield (sanic_app, sanicjwt)


class TestEndpointsSync(object):

    @pytest.yield_fixture
    def user1(self, app_with_scopes):
        sanic_app, _ = app_with_scopes
        _, response = sanic_app.test_client.post(
            "/auth", json={"username": "user1", "password": "abcxyz"}
        )
        assert response.status == 200
        yield response

    @pytest.yield_fixture
    def user2(self, app_with_scopes):
        sanic_app, _ = app_with_scopes
        _, response = sanic_app.test_client.post(
            "/auth", json={"username": "user2", "password": "abcxyz"}
        )
        assert response.status == 200
        yield response

    @pytest.yield_fixture
    def user3(self, app_with_scopes):
        sanic_app, _ = app_with_scopes
        _, response = sanic_app.test_client.post(
            "/auth", json={"username": "user3", "password": "abcxyz"}
        )
        assert response.status == 200
        yield response

    @pytest.yield_fixture
    def user4(self, app_with_scopes):
        sanic_app, _ = app_with_scopes
        _, response = sanic_app.test_client.post(
            "/auth", json={"username": "user4", "password": "abcxyz"}
        )
        assert response.status == 200
        yield response

    @pytest.yield_fixture
    def user5(self, app_with_scopes):
        sanic_app, _ = app_with_scopes
        _, response = sanic_app.test_client.post(
            "/auth", json={"username": "user5", "password": "abcxyz"}
        )
        assert response.status == 200
        yield response

    @pytest.yield_fixture
    def user6(self, app_with_scopes):
        sanic_app, _ = app_with_scopes
        _, response = sanic_app.test_client.post(
            "/auth", json={"username": "user6", "password": "abcxyz"}
        )
        assert response.status == 200
        yield response

    def test_scopes_anonymous_user(self, app_with_scopes):
        sanic_app, _ = app_with_scopes
        _, response = sanic_app.test_client.get("/")
        assert response.status == 200
        assert response.json.get("hello") == "world"

        _, response = sanic_app.test_client.get("/auth/me")
        assert response.status == 400

        _, response = sanic_app.test_client.get("/protected")
        assert response.status == 401

        _, response = sanic_app.test_client.get("/protected/scoped/1")
        assert response.status == 401

        _, response = sanic_app.test_client.get("/protected/scoped/2")
        assert response.status == 401

        _, response = sanic_app.test_client.get("/protected/scoped/3")
        assert response.status == 401

        _, response = sanic_app.test_client.get("/protected/scoped/4")
        assert response.status == 401

        _, response = sanic_app.test_client.get("/protected/scoped/5")
        assert response.status == 401

        _, response = sanic_app.test_client.get("/protected/scoped/6/1")
        assert response.status == 401

        _, response = sanic_app.test_client.get("/protected/scoped/6/foo")
        assert response.status == 401

        _, response = sanic_app.test_client.get("/protected/scoped/7/1")
        assert response.status == 401

        _, response = sanic_app.test_client.get("/protected/scoped/7/foo")
        assert response.status == 401

        _, response = sanic_app.test_client.get("/protected/scoped/8")
        assert response.status == 401

        _, response = sanic_app.test_client.get("/protected/scoped/9/1")
        assert response.status == 401

        _, response = sanic_app.test_client.get("/protected/scoped/9/foo")
        assert response.status == 401

    def test_scopes_user1(self, app_with_scopes, user1):
        sanic_app, sanicjwt = app_with_scopes
        access_token = user1.json.get(
            sanicjwt.config.access_token_name(), None
        )

        _, response = sanic_app.test_client.get("/")
        assert response.status == 200
        assert response.json.get("hello") == "world"

        _, response = sanic_app.test_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("me").get("user_id") == 1
        assert response.json.get("me").get("username") == "user1"
        assert response.json.get("me").get("scopes") == ["user"]

        _, response = sanic_app.test_client.get(
            "/protected",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is False

        _, response = sanic_app.test_client.get(
            "/protected/scoped/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True

        _, response = sanic_app.test_client.get(
            "/protected/scoped/2",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True

        _, response = sanic_app.test_client.get(
            "/protected/scoped/3",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/4",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True

        _, response = sanic_app.test_client.get(
            "/protected/scoped/5",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True

        _, response = sanic_app.test_client.get(
            "/protected/scoped/6/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True
        assert response.json.get("id") == "1"

        _, response = sanic_app.test_client.get(
            "/protected/scoped/6/foo",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True
        assert response.json.get("id") == "foo"

        _, response = sanic_app.test_client.get(
            "/protected/scoped/7/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/8",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True

        _, response = sanic_app.test_client.get(
            "/protected/scoped/9/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

    def test_scopes_user2(self, app_with_scopes, user2):
        sanic_app, sanicjwt = app_with_scopes
        access_token = user2.json.get(
            sanicjwt.config.access_token_name(), None
        )

        _, response = sanic_app.test_client.get("/")
        assert response.status == 200
        assert response.json.get("hello") == "world"

        _, response = sanic_app.test_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("me").get("user_id") == 2
        assert response.json.get("me").get("username") == "user2"
        assert response.json.get("me").get("scopes") == ["user", "admin"]

        _, response = sanic_app.test_client.get(
            "/protected",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is False

        _, response = sanic_app.test_client.get(
            "/protected/scoped/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True

        _, response = sanic_app.test_client.get(
            "/protected/scoped/2",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True

        _, response = sanic_app.test_client.get(
            "/protected/scoped/3",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True

        _, response = sanic_app.test_client.get(
            "/protected/scoped/4",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True

        _, response = sanic_app.test_client.get(
            "/protected/scoped/5",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True

        _, response = sanic_app.test_client.get(
            "/protected/scoped/6/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True
        assert response.json.get("id") == "1"

        _, response = sanic_app.test_client.get(
            "/protected/scoped/6/foo",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True
        assert response.json.get("id") == "foo"

        _, response = sanic_app.test_client.get(
            "/protected/scoped/7/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/8",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True

        _, response = sanic_app.test_client.get(
            "/protected/scoped/9/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

    def test_scopes_user3(self, app_with_scopes, user3):
        sanic_app, sanicjwt = app_with_scopes
        access_token = user3.json.get(
            sanicjwt.config.access_token_name(), None
        )

        _, response = sanic_app.test_client.get("/")
        assert response.status == 200
        assert response.json.get("hello") == "world"

        _, response = sanic_app.test_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("me").get("user_id") == 3
        assert response.json.get("me").get("username") == "user3"
        assert response.json.get("me").get("scopes") == ["user:read"]

        _, response = sanic_app.test_client.get(
            "/protected",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is False

        _, response = sanic_app.test_client.get(
            "/protected/scoped/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/2",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True

        _, response = sanic_app.test_client.get(
            "/protected/scoped/3",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/4",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/5",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/6/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/6/foo",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/7/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/8",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True

        _, response = sanic_app.test_client.get(
            "/protected/scoped/9/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

    def test_scopes_user4(self, app_with_scopes, user4):
        sanic_app, sanicjwt = app_with_scopes
        access_token = user4.json.get(
            sanicjwt.config.access_token_name(), None
        )

        _, response = sanic_app.test_client.get("/")
        assert response.status == 200
        assert response.json.get("hello") == "world"

        _, response = sanic_app.test_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("me").get("user_id") == 4
        assert response.json.get("me").get("username") == "user4"
        assert response.json.get("me").get("scopes") == ["client1"]

        _, response = sanic_app.test_client.get(
            "/protected",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is False

        _, response = sanic_app.test_client.get(
            "/protected/scoped/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/2",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/3",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/4",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/5",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/6/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/6/foo",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/7/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True
        assert response.json.get("id") == "1"

        _, response = sanic_app.test_client.get(
            "/protected/scoped/7/foo",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/8",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/9/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True
        assert response.json.get("id") == "1"

        _, response = sanic_app.test_client.get(
            "/protected/scoped/9/foo",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

    def test_scopes_user5(self, app_with_scopes, user5):
        sanic_app, sanicjwt = app_with_scopes
        access_token = user5.json.get(
            sanicjwt.config.access_token_name(), None
        )

        _, response = sanic_app.test_client.get("/")
        assert response.status == 200
        assert response.json.get("hello") == "world"

        _, response = sanic_app.test_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("me").get("user_id") == 5
        assert response.json.get("me").get("username") == "user5"
        assert response.json.get("me").get("scopes") == ["admin"]

        _, response = sanic_app.test_client.get(
            "/protected",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is False

        _, response = sanic_app.test_client.get(
            "/protected/scoped/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/2",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/3",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/4",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True

        _, response = sanic_app.test_client.get(
            "/protected/scoped/5",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/6/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/6/foo",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/7/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        _, response = sanic_app.test_client.get(
            "/protected/scoped/8",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert response.json.get("protected") is True
        assert response.json.get("scoped") is True

        _, response = sanic_app.test_client.get(
            "/protected/scoped/9/1",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403

        def test_scopes_user6(self, app_with_scopes, user6):
            sanic_app, sanicjwt = app_with_scopes
            access_token = user6.json.get(
                sanicjwt.config.access_token_name(), None
            )

            _, response = sanic_app.test_client.get("/")
            assert response.status == 200
            assert response.json.get("hello") == "world"

            _, response = sanic_app.test_client.get(
                "/auth/me",
                headers={"Authorization": "Bearer {}".format(access_token)},
            )

            assert response.status == 200
            assert response.json.get("me").get("user_id") == 5
            assert response.json.get("me").get("username") == "user5"
            assert response.json.get("me").get("scopes") is None

            _, response = sanic_app.test_client.get(
                "/protected",
                headers={"Authorization": "Bearer {}".format(access_token)},
            )

            assert response.status == 200
            assert response.json.get("protected") is True
            assert response.json.get("scoped") is False

            _, response = sanic_app.test_client.get(
                "/protected/scoped/1",
                headers={"Authorization": "Bearer {}".format(access_token)},
            )

            assert response.status == 403

            _, response = sanic_app.test_client.get(
                "/protected/scoped/2",
                headers={"Authorization": "Bearer {}".format(access_token)},
            )

            assert response.status == 403

            _, response = sanic_app.test_client.get(
                "/protected/scoped/3",
                headers={"Authorization": "Bearer {}".format(access_token)},
            )

            assert response.status == 403

            _, response = sanic_app.test_client.get(
                "/protected/scoped/4",
                headers={"Authorization": "Bearer {}".format(access_token)},
            )

            assert response.status == 200
            assert response.json.get("protected") is True
            assert response.json.get("scoped") is True

            _, response = sanic_app.test_client.get(
                "/protected/scoped/5",
                headers={"Authorization": "Bearer {}".format(access_token)},
            )

            assert response.status == 403

            _, response = sanic_app.test_client.get(
                "/protected/scoped/6/1",
                headers={"Authorization": "Bearer {}".format(access_token)},
            )

            assert response.status == 403

            _, response = sanic_app.test_client.get(
                "/protected/scoped/6/foo",
                headers={"Authorization": "Bearer {}".format(access_token)},
            )

            assert response.status == 403

            _, response = sanic_app.test_client.get(
                "/protected/scoped/7/1",
                headers={"Authorization": "Bearer {}".format(access_token)},
            )

            assert response.status == 403

            _, response = sanic_app.test_client.get(
                "/protected/scoped/8",
                headers={"Authorization": "Bearer {}".format(access_token)},
            )

            assert response.status == 200
            assert response.json.get("protected") is True
            assert response.json.get("scoped") is True

            _, response = sanic_app.test_client.get(
                "/protected/scoped/9/1",
                headers={"Authorization": "Bearer {}".format(access_token)},
            )

            assert response.status == 403
