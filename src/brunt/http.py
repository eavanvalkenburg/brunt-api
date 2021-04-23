"""Main code for brunt http."""
import json
import logging
from datetime import datetime
from abc import ABC, abstractmethod, abstractproperty
from typing import Any, Dict, Union
import requests
from requests.models import Response
from aiohttp import ClientResponse, ClientSession
from multidict import CIMultiDict

from .utils import RequestTypes
from .const import DT_FORMAT_STRING, COOKIE_DOMAIN

_LOGGER = logging.getLogger(__name__)

DEFAULT_HEADER = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://sky.brunt.co",
    "Accept-Language": "en-gb",
    "Accept": "application/vnd.brunt.v1+json",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E216",
}


class BaseBruntHTTP(ABC):
    """Base class for Brunt HTTP."""

    def __init__(self):
        """Initialize the BaseBruntHTTP object."""
        self._session = None

    def _prepare_request(self, data: dict) -> dict:
        """Prepare the payload and add the length to the header, payload might be empty."""
        # headers = DEFAULT_HEADER.copy()
        payload = ""
        headers = ""
        if "data" in data:
            payload = json.dumps(data["data"])
            headers = {"Content-Length": str(len(payload))}

        _LOGGER.debug("url: %s", data["host"] + data["path"])
        _LOGGER.debug("data: %s", payload)
        _LOGGER.debug("headers: %s", self._session.headers)
        _LOGGER.debug("request headers: %s", headers)
        return {"url": data["host"] + data["path"], "data": payload, "headers": headers}

    def _parse_response(
        self,
        response: Union[ClientResponse, Response],
        response_json: Union[dict, list],
    ) -> dict:
        """Parse the json of the response."""
        ret: Dict[str, Any] = {"result": "success"}
        _LOGGER.debug("Response json: %s", response_json)
        # if it is a list of things, then set the tag to things
        if isinstance(response_json, list):
            ret["things"] = response_json
            return ret

        if "ID" in response_json:
            ret["login"] = response_json
            return ret

        ret["thing"] = response_json
        return ret

    @abstractmethod
    def request(self, data: dict, request_type: RequestTypes) -> dict:
        """Return the request response - abstract."""
        pass

    @abstractmethod
    async def async_request(self, data: dict, request_type: RequestTypes) -> dict:
        """Return the request response - abstract."""
        pass

    @abstractproperty
    def is_logged_in(self) -> bool:
        """Return True if there is a session and the cookie is still valid."""
        pass


class BruntHttp(BaseBruntHTTP):
    """Class for brunt http calls."""

    def __init__(self, session: requests.Session = None):
        """Initialize the BruntHTTP object."""
        super().__init__()
        self._session = session if session else requests.Session()
        self._session.headers = DEFAULT_HEADER

    @property
    def is_logged_in(self) -> bool:
        """Return True if there is a session and the cookie is still valid."""
        if not self._session.cookies:
            return False

        for cookie in self._session.cookies:
            if cookie.domain == COOKIE_DOMAIN:
                return (
                    datetime.strptime(cookie.expires, DT_FORMAT_STRING)
                    > datetime.utcnow()
                )
        return False

    async def async_request(self, data: dict, request_type: RequestTypes) -> dict:
        """Raise error for using this call with sync."""
        raise NotImplementedError("You are using the sync version, please use request.")

    def request(self, data: dict, request_type: RequestTypes) -> dict:
        """Request the data.

        :param session: session object from the Requests package
        :param data: internal data of your API call
        :param request: the type of request, based on the RequestType enum
        :returns: dict with sessionid for a login and the dict of the things for the other calls, or just success for PUT
        :raises: raises errors from Requests through the raise_for_status function
        """
        resp = self._session.request(request_type.value, **self._prepare_request(data))
        # raise an error if it occured in the Request.
        resp.raise_for_status()
        # check if there is something in the response body
        if len(resp.text) == 0:
            return {"result": "success"}
        return self._parse_response(resp, resp.json())


class BruntHttpAsync(BaseBruntHTTP):
    """Class for async brunt http calls."""

    def __init__(self, session: ClientSession = None):
        """Initialize the BruntHTTP object."""
        super().__init__()
        self._session = session if session else ClientSession()
        self._session._default_headers = CIMultiDict(DEFAULT_HEADER)

    @property
    def is_logged_in(self) -> bool:
        """Return True if there is a session and the cookie is still valid."""
        if not self._session.cookie_jar:
            return False
        for cookie in self._session.cookie_jar:
            if cookie.get("domain") == COOKIE_DOMAIN:
                return (
                    datetime.strptime(cookie.get("expires"), DT_FORMAT_STRING)
                    > datetime.utcnow()
                )
        return False

    def request(self, data: dict, request_type: RequestTypes) -> dict:
        """Raise error for using this call with async."""
        raise NotImplementedError(
            "You are using the Async version, please use async_request."
        )

    async def async_request(self, data: dict, request_type: RequestTypes) -> dict:
        """Request the data.

        :param session: session object from the Requests package
        :param data: internal data of your API call
        :param request: the type of request, based on the RequestType enum
        :returns: dict with sessionid for a login and the dict of the things for the other calls, or just success for PUT
        :raises: raises errors from Requests through the raise_for_status function
        """
        async with self._session.request(
            request_type.value, **self._prepare_request(data), raise_for_status=True
        ) as resp:
            try:
                result = await resp.json(content_type=None)
            except json.JSONDecodeError:
                return {"result": "success"}
            return self._parse_response(resp, result)
