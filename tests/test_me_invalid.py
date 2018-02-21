import pytest


@pytest.fixture
def access_token(app):
    sanic_app, sanic_jwt = app
    _, response = sanic_app.test_client.post(
        '/auth', json={
            'username': 'user1',
            'password': 'abcxyz'
        })
    return response.json.get(sanic_jwt.config.access_token_name, None)


def test_me(app, access_token):
    with pytest.raises(Exception):
        sanic_app, _ = app
        _, response = sanic_app.test_client.get(
            '/auth/me',
            headers={
                'Authorization': 'Bearer {}'.format(access_token)
            })

        assert response.status == 200
