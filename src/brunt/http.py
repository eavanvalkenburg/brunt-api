"""Main code for brunt http."""
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Union, overload

import requests
from aiohttp import ClientResponse, ClientSession
from requests.models import Response

from .utils import RequestTypes

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
        self._sessionid = ""

    @property
    def _has_sessionid(self) -> bool:
        """Check whether or not the user is logged in."""
        return True if self._sessionid else False

    def _prepare_request(self, data: dict) -> dict:
        """Prepare the payload and add the length to the header, payload might be empty."""
        headers = DEFAULT_HEADER.copy()
        if self._sessionid:
            headers["Cookie"] = "skySSEIONID=" + self._sessionid

        if "data" in data:
            payload = json.dumps(data["data"])
            headers["Content-Length"] = str(len(data["data"]))
        else:
            payload = ""

        _LOGGER.debug("url: %s", data["host"] + data["path"])
        _LOGGER.debug("data: %s", payload)
        _LOGGER.debug("headers: %s", headers)
        return {"url": data["host"] + data["path"], "data": payload, "headers": headers}

    def _parse_response(
        self,
        response: Union[ClientResponse, Response],
        response_json: Union[dict, list],
    ) -> dict:
        """Parse the json of the response."""
        ret: Dict[str, Any] = {"result": "success"}
        # if it is a list of things, then set the tag to things
        if isinstance(response_json, list):
            ret["things"] = response_json
            return ret

        if "ID" in response_json:
            ret["login"] = response_json
            # if it was a login a new cookie was send back, capture the sessionid from it
            self._sessionid = response.cookies["skySSEIONID"]
            ret["cookie"] = response.cookies
            return ret

        ret["thing"] = response_json
        return ret

    @abstractmethod
    def request(self, data: dict, request_type: RequestTypes) -> dict:
        pass

    @abstractmethod
    async def async_request(self, data: dict, request_type: RequestTypes) -> dict:
        pass


class BruntHttp(BaseBruntHTTP):
    """Class for brunt http calls."""

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
        resp = requests.request(request_type.value, **self._prepare_request(data))
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
