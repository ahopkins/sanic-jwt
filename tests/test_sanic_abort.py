from sanic.exceptions import abort


def test_sanic_abort_401(app):
    sanic_app, _ = app

    @sanic_app.route("/abort")
    async def abort_request(request):
        abort(401)

    _, response = sanic_app.test_client.get('/abort')

    assert response.status == 401
