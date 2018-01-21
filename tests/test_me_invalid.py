import pytest


@pytest.fixture
def access_token(app):
    _, response = app.test_client.post(
        '/auth', json={
            'username': 'user1',
            'password': 'abcxyz'
        })
    return response.json.get(app.config.SANIC_JWT_ACCESS_TOKEN_NAME, None)


def test_me(app, access_token):
    with pytest.raises(Exception):
        _, response = app.test_client.get(
            '/auth/me',
            headers={
                'Authorization': 'Bearer {}'.format(access_token)
            })

        assert response.status == 200
