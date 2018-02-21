from . import exceptions
from . import utils
from .base import BaseDerivative
from sanic.views import HTTPMethodView
from sanic.response import json
from sanic.response import text


class BaseEndpoint(BaseDerivative, HTTPMethodView):
    def __init__(self, responses, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.responses = responses


class AuthenticateEndpoint(BaseEndpoint):
    async def options(self, request, *args, **kwargs):
        return text('', status=204)

    async def post(self, request, *args, **kwargs):
        config = self.config
        user = await utils.call(
            self.instance.auth.authenticate, request, *args, **kwargs)

        access_token, output = await self.responses.get_access_token_output(
            request, user, self.config, self.instance)

        if config.refresh_token_enabled:
            refresh_token = await utils.call(
                self.instance.auth.get_refresh_token, request, user)
            output.update({
                config.refresh_token_name: refresh_token
            })
        else:
            refresh_token = None

        output.update(self.responses.extend_authenticate(
            request, user=user, access_token=access_token,
            refresh_token=refresh_token))

        resp = self.responses.get_token_reponse(
            request, access_token, output, refresh_token=refresh_token,
            config=self.config)

        return resp


class RetrieveUserEndpoint(BaseEndpoint):
    async def get(self, request, *args, **kwargs):
        config = self.config
        if not hasattr(self.instance.auth, 'retrieve_user'):
            raise exceptions.MeEndpointNotSetup()

        try:
            payload = self.instance.auth.extract_payload(request)
            user = await utils.call(
                self.instance.auth.retrieve_user, request, payload)
        except exceptions.MissingAuthorizationCookie:
            user = None
            payload = None

        if not user:
            me = None
        else:
            if isinstance(user, dict):
                me = user
            elif hasattr(user, 'to_dict'):
                me = await utils.call(user.to_dict)

        output = {
            'me': me
        }

        output.update(self.responses.extend_retrieve_user(
            request, user=user, payload=payload,))

        resp = json(output)

        if payload is None and config.cookie_set:
            key = config.cookie_access_token_name
            del resp.cookies[key]

        return resp


class VerifyEndpoint(BaseEndpoint):
    async def get(self, request, *args, **kwargs):
        is_valid, status, reason = self.instance.auth.verify(
            request, *args, **kwargs)

        output = {
            'valid': is_valid
        }

        if reason:
            output.update({'reason': reason})

        output.update(self.responses.extend_verify(request,))
        return json(output, status=status)


class RefreshEndpoint(BaseEndpoint):
    async def options(self, request, *args, **kwargs):
        return text('', status=204)

    async def post(self, request, *args, **kwargs):
        # TODO:
        # - Add more exceptions
        payload = self.instance.auth.extract_payload(request, verify=False)
        user = await utils.call(
            self.instance.auth.retrieve_user, request, payload=payload)
        user_id = await self.instance.auth._get_user_id(user)
        refresh_token = await utils.call(
            self.instance.auth.retrieve_refresh_token,
            request=request,
            user_id=user_id)
        if isinstance(refresh_token, bytes):
            refresh_token = refresh_token.decode('utf-8')
        refresh_token = str(refresh_token)
        purported_token = await self.instance.auth \
            .retrieve_refresh_token_from_request(request)

        if refresh_token != purported_token:
            raise exceptions.AuthenticationFailed()

        access_token, output = await self.responses.get_access_token_output(
            request, user, self.config, self.instance)

        output.update(self.responses.extend_refresh(
            request, user=user, access_token=access_token,
            refresh_token=refresh_token, purported_token=purported_token,
            payload=payload,))

        resp = self.responses.get_token_reponse(request, access_token, output,
                                                config=self.config)

        return resp
