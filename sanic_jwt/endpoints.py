from sanic.response import json, text
from sanic.views import HTTPMethodView

from . import exceptions, utils
from .base import BaseDerivative
from .decorators import protected


class BaseEndpoint(BaseDerivative, HTTPMethodView):
    def __init__(self, responses, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.responses = responses

    async def options(self, request, *args, **kwargs):
        return text("", status=204)

    async def do_incoming(self, request, args, kwargs):
        return request, args, kwargs

    async def do_output(self, output):
        return output

    async def do_response(self, response):
        return response


class AuthenticateEndpoint(BaseEndpoint):
    async def post(self, request, *args, **kwargs):
        request, args, kwargs = await self.do_incoming(request, args, kwargs)

        config = self.config
        user = await utils.call(
            self.instance.auth.authenticate, request, *args, **kwargs
        )

        access_token, output = await self.responses.get_access_token_output(
            request, user, self.config, self.instance
        )

        if config.refresh_token_enabled():
            refresh_token = await utils.call(
                self.instance.auth.generate_refresh_token, request, user
            )
            output.update({config.refresh_token_name(): refresh_token})
        else:
            refresh_token = None

        output.update(
            self.responses.extend_authenticate(
                request,
                user=user,
                access_token=access_token,
                refresh_token=refresh_token,
            )
        )

        output = await self.do_output(output)

        resp = self.responses.get_token_reponse(
            request,
            access_token,
            output,
            refresh_token=refresh_token,
            config=self.config,
        )

        return await self.do_response(resp)


class RetrieveUserEndpoint(BaseEndpoint):
    async def get(self, request, *args, **kwargs):
        request, args, kwargs = await self.do_incoming(request, args, kwargs)

        config = self.config
        if not hasattr(self.instance.auth, "retrieve_user"):
            # NOTE: this condition is only true if `retrieve_user` is wipped
            # out of the `Authentication` class, so it won't happen "easily".
            raise exceptions.MeEndpointNotSetup()  # noqa

        payload = self.instance.auth.extract_payload(request)
        user = await utils.call(
            self.instance.auth.retrieve_user, request, payload
        )

        if not user:  # noqa
            me = None
        else:
            if isinstance(user, dict):
                me = user
            elif hasattr(user, "to_dict"):
                me = await utils.call(user.to_dict)
            else:
                # implementations ago there was an error where "me" was
                # being used before assignment, so this exception is raised.
                # it'll stay here for now, with a noqa flag
                raise exceptions.InvalidRetrieveUserObject  # noqa

        output = {"me": me}

        output.update(
            self.responses.extend_retrieve_user(
                request, user=user, payload=payload
            )
        )

        output = await self.do_output(output)

        resp = json(output)

        if payload is None and config.cookie_set():  # noqa
            key = config.cookie_access_token_name()
            del resp.cookies[key]

        return await self.do_response(resp)


class VerifyEndpoint(BaseEndpoint):
    async def get(self, request, *args, **kwargs):
        request, args, kwargs = await self.do_incoming(request, args, kwargs)

        is_valid, status, reason = self.instance.auth._verify(
            request, raise_missing=True, *args, **kwargs
        )

        output = {"valid": is_valid}

        if reason:
            if not isinstance(reason, list):  # noqa
                reason = [reason]
            output.update({"reasons": reason})

        if not is_valid:
            output.update({"exception": exceptions.InvalidToken.__name__})

        output.update(self.responses.extend_verify(request))
        output = await self.do_output(output)
        resp = json(output, status=status)

        return await self.do_response(resp)


class RefreshEndpoint(BaseEndpoint):
    decorators = [protected(verify_exp=False)]

    async def post(self, request, *args, **kwargs):
        request, args, kwargs = await self.do_incoming(request, args, kwargs)

        # TODO:
        # - Add more exceptions
        payload = self.instance.auth.extract_payload(request, verify=False)

        try:
            user = await utils.call(
                self.instance.auth.retrieve_user, request, payload=payload
            )
        except exceptions.MeEndpointNotSetup:
            message = "Refresh tokens have not been enabled properly."
            "Perhaps you forgot to initialize with a retrieve_user handler?"
            raise exceptions.RefreshTokenNotImplemented(message=message)

        user_id = await self.instance.auth._get_user_id(user)
        refresh_token = await utils.call(
            self.instance.auth.retrieve_refresh_token,
            request=request,
            user_id=user_id,
        )
        if isinstance(refresh_token, bytes):
            refresh_token = refresh_token.decode("utf-8")

        token = await self.instance.auth.retrieve_refresh_token_from_request(
            request
        )

        if refresh_token != token:
            raise exceptions.AuthenticationFailed()

        access_token, output = await self.responses.get_access_token_output(
            request, user, self.config, self.instance
        )

        output.update(
            self.responses.extend_refresh(
                request,
                user=user,
                access_token=access_token,
                refresh_token=refresh_token,
                purported_token=token,
                payload=payload,
            )
        )
        output = await self.do_output(output)

        resp = self.responses.get_token_reponse(
            request, access_token, output, config=self.config
        )

        return await self.do_response(resp)
