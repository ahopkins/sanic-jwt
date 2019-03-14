import pytest


@pytest.fixture
def access_tokens(app_with_bp):
    app, app_int, bp, bp_init = app_with_bp
    _, response1 = app.test_client.post(
        app_int._get_url_prefix(),
        json={"username": "user1", "password": "abcxyz"},
    )
    _, response2 = app.test_client.post(
        bp_init._get_url_prefix() + "/",
        json={"username": "user2", "password": "abcxyz"},
    )

    token1 = response1.json.get(app_int.config.access_token_name(), None)
    token2 = response2.json.get(bp_init.config.access_token_name(), None)

    return (token1, token2)


# def test_verify_token1_on_app(app_with_bp, access_tokens):
#     app, _, _, _ = app_with_bp
#     token, _ = access_tokens
#     _, response = app.test_client.get(
#         '/auth/verify', headers={
#             'Authorization': 'Bearer {}'.format(token)
#         })

#     assert response.status == 200
#     assert response.json.get('valid') is True


# def test_protected(self, app, access_token):
#         _, response = self.get('/protected', app, access_token)

#         assert response.status == 200
#         assert response.json.get('protected') is True
