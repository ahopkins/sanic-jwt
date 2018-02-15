import binascii
import os
from pathlib import Path

import pytest
from sanic import Sanic
from sanic.response import json

from sanic_jwt import Initialize, exceptions
from sanic_jwt.decorators import protected


@pytest.yield_fixture
def public_rsa_key():
    yield Path(__file__).parent / 'resources' / 'rsa-test-public.pem'


@pytest.yield_fixture
def private_rsa_key():
    yield Path(__file__).parent / 'resources' / 'rsa-test-key.pem'


@pytest.yield_fixture
def public_ec_key():
    yield Path(__file__).parent / 'resources' / 'ec-test-public.pem'


@pytest.yield_fixture
def private_ec_key():
    yield Path(__file__).parent / 'resources' / 'ec-test-key.pem'


async def authenticate(request, *args, **kwargs):
    return {'user_id': 1}


def test_jwt_rsa_crypto_from_path_object(public_rsa_key, private_rsa_key):
    app = Sanic()

    sanicjwt = Initialize(
        app,
        authenticate=authenticate,
        public_key=public_rsa_key,
        private_key=private_rsa_key,
        algorithm='RS256')

    @app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    _, response = app.test_client.post(
        '/auth', json={
            'username': 'foo',
            'password': 'bar'
        })

    assert response.status == 200

    access_token = response.json.get(sanicjwt.config.access_token_name, None)

    assert access_token is not None

    _, response = app.test_client.get(
        '/protected/', headers={
            'Authorization': 'Bearer {}'.format(access_token)
        })

    assert response.status == 200
    assert response.json.get('protected') is True


def test_jwt_rsapss_crypto_from_path_object(public_rsa_key, private_rsa_key):
    app = Sanic()

    sanicjwt = Initialize(
        app,
        authenticate=authenticate,
        secret=public_rsa_key,
        private_key=private_rsa_key,
        algorithm='PS256')

    @app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    _, response = app.test_client.post(
        '/auth', json={
            'username': 'foo',
            'password': 'bar'
        })

    assert response.status == 200

    access_token = response.json.get(sanicjwt.config.access_token_name, None)

    assert access_token is not None

    _, response = app.test_client.get(
        '/protected/',
        headers={'Authorization': 'Bearer {}'.format(access_token)})

    assert response.status == 200
    assert response.json.get('protected') is True


def test_jwt_ec_crypto_from_path_object(public_ec_key, private_ec_key):
    app = Sanic()

    sanicjwt = Initialize(
        app,
        authenticate=authenticate,
        public_key=public_ec_key,
        private_key=private_ec_key,
        algorithm='ES256')

    @app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    _, response = app.test_client.post(
        '/auth', json={
            'username': 'foo',
            'password': 'bar'
        })

    assert response.status == 200

    access_token = response.json.get(sanicjwt.config.access_token_name, None)

    assert access_token is not None

    _, response = app.test_client.get(
        '/protected/',
        headers={'Authorization': 'Bearer {}'.format(access_token)})

    assert response.status == 200
    assert response.json.get('protected') is True


def test_jwt_rsa_crypto_from_fullpath_as_str(public_rsa_key, private_rsa_key):
    app = Sanic()

    sanicjwt = Initialize(
        app,
        authenticate=authenticate,
        secret=str(public_rsa_key),
        private_key=str(private_rsa_key),
        algorithm='RS384')

    @app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    _, response = app.test_client.post(
        '/auth', json={
            'username': 'foo',
            'password': 'bar'
        })

    assert response.status == 200

    access_token = response.json.get(sanicjwt.config.access_token_name, None)

    assert access_token is not None

    _, response = app.test_client.get(
        '/protected/',
        headers={'Authorization': 'Bearer {}'.format(access_token)})

    assert response.status == 200
    assert response.json.get('protected') is True


def test_jwt_rsapss_crypto_from_fullpath_as_str(public_rsa_key, private_rsa_key):
    app = Sanic()

    sanicjwt = Initialize(
        app,
        authenticate=authenticate,
        public_key=str(public_rsa_key),
        private_key=str(private_rsa_key),
        algorithm='PS384')

    @app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    _, response = app.test_client.post(
        '/auth', json={
            'username': 'foo',
            'password': 'bar'
        })

    assert response.status == 200

    access_token = response.json.get(sanicjwt.config.access_token_name, None)

    assert access_token is not None

    _, response = app.test_client.get(
        '/protected/',
        headers={'Authorization': 'Bearer {}'.format(access_token)})

    assert response.status == 200
    assert response.json.get('protected') is True


def test_jwt_ec_crypto_from_fullpath_as_str(public_ec_key, private_ec_key):
    app = Sanic()

    sanicjwt = Initialize(
        app,
        authenticate=authenticate,
        secret=str(public_ec_key),
        private_key=str(private_ec_key),
        algorithm='ES384')

    @app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    _, response = app.test_client.post(
        '/auth', json={
            'username': 'foo',
            'password': 'bar'
        })

    assert response.status == 200

    access_token = response.json.get(sanicjwt.config.access_token_name, None)

    assert access_token is not None

    _, response = app.test_client.get(
        '/protected/',
        headers={'Authorization': 'Bearer {}'.format(access_token)})

    assert response.status == 200
    assert response.json.get('protected') is True


def test_jwt_rsa_crypto_from_str(public_rsa_key, private_rsa_key):
    app = Sanic()

    sanicjwt = Initialize(
        app,
        authenticate=authenticate,
        public_key=public_rsa_key.read_text(),
        private_key=private_rsa_key.read_text(),
        algorithm='RS512')

    @app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    _, response = app.test_client.post(
        '/auth', json={
            'username': 'foo',
            'password': 'bar'
        })

    assert response.status == 200

    access_token = response.json.get(sanicjwt.config.access_token_name, None)

    assert access_token is not None

    _, response = app.test_client.get(
        '/protected/',
        headers={'Authorization': 'Bearer {}'.format(access_token)})

    assert response.status == 200
    assert response.json.get('protected') is True


def test_jwt_rsapss_crypto_from_str(public_rsa_key, private_rsa_key):
    app = Sanic()

    sanicjwt = Initialize(
        app,
        authenticate=authenticate,
        secret=public_rsa_key.read_text(),
        private_key=private_rsa_key.read_text(),
        algorithm='PS512')

    @app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    _, response = app.test_client.post(
        '/auth', json={
            'username': 'foo',
            'password': 'bar'
        })

    assert response.status == 200

    access_token = response.json.get(sanicjwt.config.access_token_name, None)

    assert access_token is not None

    _, response = app.test_client.get(
        '/protected/',
        headers={'Authorization': 'Bearer {}'.format(access_token)})

    assert response.status == 200
    assert response.json.get('protected') is True


def test_jwt_ec_crypto_from_str(public_ec_key, private_ec_key):
    app = Sanic()

    sanicjwt = Initialize(
        app,
        authenticate=authenticate,
        public_key=public_ec_key.read_text(),
        private_key=private_ec_key.read_text(),
        algorithm='ES512')

    @app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    _, response = app.test_client.post(
        '/auth', json={
            'username': 'foo',
            'password': 'bar'
        })

    assert response.status == 200

    access_token = response.json.get(sanicjwt.config.access_token_name, None)

    assert access_token is not None

    _, response = app.test_client.get(
        '/protected/',
        headers={'Authorization': 'Bearer {}'.format(access_token)})

    assert response.status == 200
    assert response.json.get('protected') is True


def test_jwt_crypto_wrong_keys():
    app = Sanic()

    Initialize(
        app,
        authenticate=authenticate,
        public_key=str(binascii.hexlify(os.urandom(48)), 'utf-8'),
        private_key=str(binascii.hexlify(os.urandom(48)), 'utf-8'),
        algorithm='RS256')

    @app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    _, response = app.test_client.post(
        '/auth', json={
            'username': 'foo',
            'password': 'bar'
        })

    assert response.status == 500


def test_jwt_crypto_missing_private_key(public_rsa_key):
    with pytest.raises(exceptions.RequiredKeysNotFound):
        Initialize(
            Sanic(),
            authenticate=lambda: True,
            secret=public_rsa_key,
            algorithm='RS256')
