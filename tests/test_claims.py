import jwt
from datetime import datetime, timedelta
from freezegun import freeze_time


class TestClaimsExp:

    def test_unexpired(self, app):
        sanic_app, sanic_jwt = app
        _, response = sanic_app.test_client.post(
            "/auth", json={"username": "user1", "password": "abcxyz"}
        )

        access_token = response.json.get(
            sanic_jwt.config.access_token_name(), None
        )
        payload = jwt.decode(access_token, sanic_jwt.config.secret())
        exp = payload.get("exp", None)

        assert "exp" in payload

        exp = datetime.utcfromtimestamp(exp)

        assert isinstance(exp, datetime)
        assert datetime.utcnow() < exp

        _, response = sanic_app.test_client.get(
            "/protected",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200

    def test_expired(self, app):
        sanic_app, sanic_jwt = app
        _, response = sanic_app.test_client.post(
            "/auth", json={"username": "user1", "password": "abcxyz"}
        )

        access_token = response.json.get(
            sanic_jwt.config.access_token_name(), None
        )
        payload = jwt.decode(access_token, sanic_jwt.config.secret())
        exp = payload.get("exp", None)

        assert "exp" in payload

        exp = datetime.utcfromtimestamp(exp)

        with freeze_time(datetime.utcnow() + timedelta(seconds=(60 * 35))):
            assert isinstance(exp, datetime)
            assert datetime.utcnow() > exp

            _, response = sanic_app.test_client.get(
                "/protected",
                headers={"Authorization": "Bearer {}".format(access_token)},
            )

            assert response.status == 403
            assert "Signature has expired" in response.json.get("reasons")

    def test_exp_configuration(self, app_with_extended_exp):
        sanic_app, sanic_jwt = app_with_extended_exp
        _, response = sanic_app.test_client.post(
            "/auth", json={"username": "user1", "password": "abcxyz"}
        )

        access_token = response.json.get(
            sanic_jwt.config.access_token_name(), None
        )
        payload = jwt.decode(
            access_token, sanic_jwt.config.secret(), verify=False
        )
        exp = payload.get("exp", None)
        exp = datetime.utcfromtimestamp(exp)

        with freeze_time(datetime.utcnow() + timedelta(seconds=(60 * 35))):
            assert isinstance(exp, datetime)
            assert datetime.utcnow() < exp

            _, response = sanic_app.test_client.get(
                "/protected",
                headers={"Authorization": "Bearer {}".format(access_token)},
            )
            assert response.status == 200

    def test_leeway_configuration(self, app_with_leeway):
        sanic_app, sanic_jwt = app_with_leeway
        _, response = sanic_app.test_client.post(
            "/auth", json={"username": "user1", "password": "abcxyz"}
        )

        access_token = response.json.get(
            sanic_jwt.config.access_token_name(), None
        )
        payload = jwt.decode(
            access_token, sanic_jwt.config.secret(), verify=False
        )
        exp = payload.get("exp", None)
        exp = datetime.utcfromtimestamp(exp)

        with freeze_time(datetime.utcnow() + timedelta(seconds=(60 * 35 + 1))):
            _, response = sanic_app.test_client.get(
                "/protected",
                headers={"Authorization": "Bearer {}".format(access_token)},
            )
            assert response.status == 403

        with freeze_time(datetime.utcnow() + timedelta(seconds=(60 * 35 - 1))):
            _, response = sanic_app.test_client.get(
                "/protected",
                headers={"Authorization": "Bearer {}".format(access_token)},
            )
            assert response.status == 200

    def test_nbf(self, app_with_nbf):
        sanic_app, sanic_jwt = app_with_nbf
        _, response = sanic_app.test_client.post(
            "/auth", json={"username": "user1", "password": "abcxyz"}
        )

        access_token = response.json.get(
            sanic_jwt.config.access_token_name(), None
        )
        payload = jwt.decode(
            access_token, sanic_jwt.config.secret(), verify=False
        )
        exp = payload.get("exp", None)
        exp = datetime.utcfromtimestamp(exp)

        assert "nbf" in payload
        assert isinstance(payload.get("nbf"), int)

        _, response = sanic_app.test_client.get(
            "/protected",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 403
        assert "The token is not yet valid (nbf)" in response.json.get(
            "reasons"
        )

        with freeze_time(datetime.utcnow() + timedelta(seconds=(60 * 5 - 1))):
            _, response = sanic_app.test_client.get(
                "/protected",
                headers={"Authorization": "Bearer {}".format(access_token)},
            )

            assert response.status == 403

        with freeze_time(datetime.utcnow() + timedelta(seconds=(60 * 5 + 1))):
            _, response = sanic_app.test_client.get(
                "/protected",
                headers={"Authorization": "Bearer {}".format(access_token)},
            )

            assert response.status == 200

    def test_iat(self, app_with_iat):
        sanic_app, sanic_jwt = app_with_iat
        _, response = sanic_app.test_client.post(
            "/auth", json={"username": "user1", "password": "abcxyz"}
        )

        access_token = response.json.get(
            sanic_jwt.config.access_token_name(), None
        )
        payload = jwt.decode(
            access_token, sanic_jwt.config.secret(), verify=False
        )

        assert "iat" in payload
        assert isinstance(payload.get("iat"), int)

        _, response = sanic_app.test_client.get(
            "/protected",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200

    def test_iss(self, app_with_iss):
        sanic_app, sanic_jwt = app_with_iss
        _, response = sanic_app.test_client.post(
            "/auth", json={"username": "user1", "password": "abcxyz"}
        )

        access_token = response.json.get(
            sanic_jwt.config.access_token_name(), None
        )
        payload = jwt.decode(
            access_token, sanic_jwt.config.secret(), verify=False
        )

        assert "iss" in payload
        assert isinstance(payload.get("iss"), str)

        _, response = sanic_app.test_client.get(
            "/protected",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert payload.get("iss") == "issuingserver"

    def test_aud(self, app_with_aud):
        sanic_app, sanic_jwt = app_with_aud
        _, response = sanic_app.test_client.post(
            "/auth", json={"username": "user1", "password": "abcxyz"}
        )

        access_token = response.json.get(
            sanic_jwt.config.access_token_name(), None
        )
        payload = jwt.decode(
            access_token, sanic_jwt.config.secret(), verify=False
        )

        assert "aud" in payload
        assert isinstance(payload.get("aud"), str)

        _, response = sanic_app.test_client.get(
            "/protected",
            headers={"Authorization": "Bearer {}".format(access_token)},
        )

        assert response.status == 200
        assert payload.get("aud") == "clientserver"
