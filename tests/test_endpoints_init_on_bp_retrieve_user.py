from sanic_jwt import Initialize
import pytest


@pytest.fixture
def app_with_retrieve_user_on_bp(
    authenticate, retrieve_user, app_with_bp_setup_without_init
):
    app, bp = app_with_bp_setup_without_init
    sanicjwt = Initialize(
        bp, app=app, authenticate=authenticate, retrieve_user=retrieve_user, debug=True
    )
    app.blueprint(bp)
    return app, sanicjwt, bp


def test_me(app_with_retrieve_user_on_bp):
    app, sanicjwt, bp = app_with_retrieve_user_on_bp
    _, response = app.test_client.post(
        sanicjwt._get_url_prefix() + "/",
        json={"username": "user1", "password": "abcxyz"},
    )

    assert response.status == 200

    access_token = response.json.get(sanicjwt.config.access_token_name(), None)

    _, response = app.test_client.get(
        sanicjwt._get_url_prefix() + "/me",
        headers={"Authorization": "Bearer {}".format(access_token)},
    )

    assert response.status == 200
    assert response.json.get("me").get("user_id") == 1
