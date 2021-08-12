from sanic.exceptions import abort

from sanic_jwt.decorators import protected


def test_abort_called_in_endpoint(app):
    sanic_app, sanic_jwt = app

    @sanic_app.route("/abort", methods=["GET"])
    @protected()
    async def test(request):
        abort(400, "Aborted request")

    _, response = sanic_app.test_client.post(
        "/auth", json={"username": "user1", "password": "abcxyz"}
    )

    access_token = response.json.get(
        sanic_jwt.config.access_token_name(), None
    )

    _, response = sanic_app.test_client.get(
        "/abort", headers={"Authorization": "Bearer {}".format(access_token)}
    )

    assert response.status == 400
    assert b"Aborted request" in response.body
