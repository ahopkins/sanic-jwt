import jwt


def test_wrong_token(app):
    sanic_app, sanic_jwt = app

    payload = {"foo": "bar"}

    access_token = jwt.encode(
        payload,
        sanic_jwt.config.secret(),
        algorithm=sanic_jwt.config.algorithm(),
    )

    _, response = sanic_app.test_client.get(
        "/protected",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    print(response.json)
    assert response.status == 200
