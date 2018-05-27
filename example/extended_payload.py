from sanic import Sanic
from sanic_jwt import exceptions
from sanic_jwt import Authentication
from sanic_jwt import Initialize


class User:

    def __init__(self, id, username, password):
        self.user_id = id
        self.username = username
        self.password = password

    def __repr__(self):
        return "User(id='{}')".format(self.user_id)

    def to_dict(self):
        return {"user_id": self.user_id, "username": self.username}


users = [User(1, "user1", "abcxyz"), User(2, "user2", "abcxyz")]

username_table = {u.username: u for u in users}
userid_table = {u.user_id: u for u in users}


class MyAuthentication(Authentication):

    async def extend_payload(self, payload, *args, **kwargs):
        payload.update({"app_name": self.app.name})
        return payload

    async def authenticate(self, request, *args, **kwargs):
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


app = Sanic("test")
Initialize(app, authentication_class=MyAuthentication)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8888)
