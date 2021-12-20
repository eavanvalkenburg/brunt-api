"""Main code for brunt http."""
import json
import logging
from abc import abstractmethod, abstractproperty
from datetime import datetime
from typing import Union

import requests
from aiohttp import ClientSession
from multidict import CIMultiDict
from requests.utils import CaseInsensitiveDict

from .const import COOKIE_DOMAIN, DT_FORMAT_STRING
from .utils import RequestTypes

_LOGGER = logging.getLogger(__name__)

DEFAULT_HEADER = CaseInsensitiveDict(
    {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://sky.brunt.co",
        "Accept-Language": "en-gb",
        "Accept": "application/vnd.brunt.v1+json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_3 like Mac OS X) \
AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E216",
    }
)


class BaseBruntHTTP:
    """Base class for Brunt HTTP."""

    @staticmethod
    def _prepare_request(data: dict) -> dict:
        """Prepare the payload and add the length to the header, payload might be empty."""
        payload = ""
        headers = {}
        if "data" in data:
            payload = json.dumps(data["data"])
            headers = {"Content-Length": str(len(payload))}

        return {"url": data["host"] + data["path"], "data": payload, "headers": headers}

    @abstractmethod
    def request(self, data: dict, request_type: RequestTypes) -> Union[dict, list]:
        """Return the request response - abstract."""

    @abstractmethod
    async def async_request(
        self, data: dict, request_type: RequestTypes
    ) -> Union[dict, list]:
        """Return the request response - abstract."""

    @abstractproperty
    def is_logged_in(self) -> bool:
        """Return True if there is a session and the cookie is still valid."""


class BruntHttp(BaseBruntHTTP):
    """Class for brunt http calls."""

    def __init__(self, session: requests.Session = None):
        """Initialize the BruntHTTP object."""
        self.session = session if session else requests.Session()
        self.session.headers = DEFAULT_HEADER

    @property
    def is_logged_in(self) -> bool:
        """Return True if there is a session and the cookie is still valid."""
        if not self.session.cookies:
            return False

        for cookie in self.session.cookies:
            if cookie.domain == COOKIE_DOMAIN:
                if cookie.expires is not None:
                    return (
                        datetime.strptime(str(cookie.expires), DT_FORMAT_STRING)
                        > datetime.utcnow()
                    )
        return False

    async def async_request(
        self, data: dict, request_type: RequestTypes
    ) -> Union[dict, list]:
        """Raise error for using this call with sync."""
        raise NotImplementedError("You are using the sync version, please use request.")

    def request(self, data: dict, request_type: RequestTypes) -> Union[dict, list]:
        """Request the data.

        :param session: session object from the Requests package
        :param data: internal data of your API call
        :param request: the type of request, based on the RequestType enum
        :returns: dict with sessionid for a login and the dict of the things for the other calls,
            or just success for PUT
        :raises: raises errors from Requests through the raise_for_status function
        """
        resp = self.session.request(
            request_type.value, **BaseBruntHTTP._prepare_request(data)
        )
        # raise an error if it occured in the Request.
        resp.raise_for_status()
        # check if there is something in the response body
        if len(resp.text) == 0:
            return {"result": "success"}
        return resp.json()


class BruntHttpAsync(BaseBruntHTTP):
    """Class for async brunt http calls."""

    def __init__(self, session: ClientSession = None):
        """Initialize the BruntHTTP object."""
        self.session = session if session else ClientSession()
        self.session._default_headers = CIMultiDict(DEFAULT_HEADER)

    @property
    def is_logged_in(self) -> bool:
        """Return True if there is a session and the cookie is still valid."""
        if not self.session.cookie_jar:
            return False
        for cookie in self.session.cookie_jar:
            if cookie.get("domain") == COOKIE_DOMAIN:
                if cookie.get("expires") is not None:
                    return (
                        datetime.strptime(str(cookie.get("expires")), DT_FORMAT_STRING)
                        > datetime.utcnow()
                    )
        return False

    def request(self, data: dict, request_type: RequestTypes) -> Union[dict, list]:
        """Raise error for using this call with async."""
        raise NotImplementedError(
            "You are using the Async version, please use async_request."
        )

    async def async_request(
        self, data: dict, request_type: RequestTypes
    ) -> Union[dict, list]:
        """Request the data.

        :param session: session object from the Requests package
        :param data: internal data of your API call
        :param request: the type of request, based on the RequestType enum
        :returns: dict with sessionid for a login and the dict of the things for
            the other calls, or just success for PUT
        :raises: raises errors from Requests through the raise_for_status function
        """
        async with self.session.request(
            request_type.value,
            **BaseBruntHTTP._prepare_request(data),
            raise_for_status=True
        ) as resp:
            try:
                return await resp.json(content_type=None)
            except json.JSONDecodeError:
                return {"result": "success"}
