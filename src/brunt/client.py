"""Main code for brunt api package."""
from __future__ import annotations

import logging
from abc import ABC
from datetime import datetime
from types import TracebackType
from typing import Any, List, Optional, Type

from aiohttp.client import ClientSession
from requests import Session

from .const import (MAIN_HOST, MAIN_THINGS_PATH, REQUEST_POSITION_KEY,
                    THINGS_HOST)
from .http import BruntHttp, BruntHttpAsync
from .utils import RequestTypes

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


class BaseClient(ABC):
    """Base class for clients."""

    def __init__(self, username: str = None, password: str = None):
        """Construct for the API wrapper.

        If you supply username and password here, they are stored, but not used.
        Auto logging in then does work when calling another method, no explicit login needed.

        :param username: the username of your Brunt account
        :param password: the password of your Brunt account
        """
        self._user: str = username
        self._pass: str = password
        self._things: List = []
        self._lastlogin: Optional[datetime] = None

    def _prepare_login(self, username: str = None, password: str = None) -> dict:
        """Prepare the login info."""
        _LOGGER.debug("Prepare Login")
        self._user = username if username else self._user
        self._pass = password if password else self._pass
        if not self._user or not self._pass:
            raise NameError(
                "Please login first using the login function, with username and password"
            )
        return {
            "data": {"ID": self._user, "PASS": self._pass},
            "path": "/session",
            "host": MAIN_HOST,
        }

    def _prepare_state(self, **kwargs) -> dict:
        """Prepare the data for a Get State call."""
        if "thingUri" in kwargs:
            return {"path": f"/thing{kwargs['thingUri']}", "host": THINGS_HOST}

        if "thing" in kwargs:
            for thing in self._things:
                if thing.get("NAME", None) == kwargs["thing"] and "thingUri" in thing:
                    return {"path": f"/thing{thing['thingUri']}", "host": THINGS_HOST}
            raise ValueError("Unknown thing: " + kwargs["thing"])

        raise SyntaxError(
            "Please provide either the 'thing' name or the 'thingUri', the thingUri is used first when given."
        )

    def _prepare_change_key(self, **kwargs) -> dict:
        """Prepare the data for the change key call."""
        key = kwargs.get("key", None)
        if not key:
            raise SyntaxError("Please provide a key to change")
        value = kwargs.get("value", None)
        if not value:
            raise SyntaxError("Please provide a value to change to")
        if key.lower().find("position"):
            if int(value) < 0 or int(value) > 100:
                raise ValueError("Please set the position between 0 and 100.")

        if "thingUri" in kwargs:
            return {
                "data": {str(key): str(value)},
                "path": f"/thing{kwargs['thingUri']}",
                "host": THINGS_HOST,
            }

        if "thing" in kwargs:
            for thing in self._things:
                if thing.get("NAME", None) == kwargs["thing"] and "thingUri" in thing:
                    return {
                        "data": {str(key): str(value)},
                        "path": f"/thing{thing['thingUri']}",
                        "host": THINGS_HOST,
                    }
            raise ValueError("Unknown thing: " + kwargs["thing"])

        raise SyntaxError(
            "Please provide either the 'thing' name or the 'thingUri', the thingUri is used first when given."
        )


class BruntClient(BaseClient):
    """Class for the Brunt API."""

    def __init__(
        self,
        username: str = None,
        password: str = None,
        session: Session = None,
    ):
        """Construct for the API wrapper.

        If you supply username and password here, they are stored, but not used.
        Auto logging in then does work when calling another method, no explicit login needed.

        :param username: the username of your Brunt account
        :param password: the password of your Brunt account
        """
        super().__init__(username, password)
        self._http = BruntHttp(session=session)

    def __enter__(self) -> BruntClient:
        """Enter the context manager."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Exit the context manager."""
        self.close()

    def close(self) -> None:
        """Close the session."""
        self._http._session.close()

    def login(self, username: str = None, password: str = None) -> bool:
        """Login method using username and password.

        :param username: the username of your Brunt account
        :param password: the password of your Brunt account
        :return: True if successfull
        :raises: errors from Requests call
        """
        self._http.request(self._prepare_login(username, password), RequestTypes.POST)
        self._lastlogin = datetime.utcnow()
        return True

    def get_things(self, force: bool = False) -> list:
        """Get the things registered in your account.

        :return: dict with things registered in the logged in account and API call status
        """
        if not self._things or force:
            return self._get_things()
        return self._things

    def _get_things(self) -> list:
        """Check if there are things in memory, otherwise first do the getThings call and then return _things.

        :return: dict with things registered (without API call status)
        """
        if not self._http.is_logged_in:
            self.login()
        resp = self._http.request(MAIN_THINGS_PATH, RequestTypes.GET)
        self._things = resp["things"]
        return self._things

    def get_state(self, **kwargs) -> dict:
        """Get the state of a thing.

        :param thing: a string with the name of the thing, which is then checked using getThings.
        :param thingUri: Uri (string) of the thing you are getting the state from, not checked against getThings.
        :return: a dict with the state of the Thing.
        :raises: ValueError if the requested thing does not exists. NameError if not logged in. SyntaxError when
            not exactly one of the params is given.
        """
        if not self._http.is_logged_in:
            self.login()
        self.get_things()
        return self._http.request(self._prepare_state(**kwargs), RequestTypes.GET)

    def change_key(self, **kwargs) -> dict:
        """Change a variable of the thing.  Mostly included for future additions.

        :param key: The value you want to change
        :param value: The new value
        :param thing: a string with the name of the thing, which is then checked using getThings.
        :param thingUri: Uri (string) of the thing you are getting the state from, not checked against getThings.
        :return: a dict with the state of the Thing.
        :raises: ValueError if the requested thing does not exists or the position is not between 0 and 100.
            NameError if not logged in. SyntaxError when not exactly one of the params is given.
        """
        if not self._http.is_logged_in:
            self.login()
        self.get_things()
        return self._http.request(self._prepare_change_key(**kwargs), RequestTypes.PUT)

    def change_request_position(self, request_position, **kwargs) -> dict:
        """Change the position of the thing.

        :param request_position: The new position for the slide (0-100)
        :param thing: a string with the name of the thing, which is then checked using getThings.
        :param thingUri: Uri (string) of the thing you are getting the state from, not checked against getThings.
        :return: a dict with the state of the Thing.
        :raises: ValueError if the requested thing does not exists or the position is not between 0 and 100.
            NameError if not logged in. SyntaxError when not exactly one of the params is given.
        """
        kwargs["key"] = REQUEST_POSITION_KEY
        kwargs["value"] = request_position
        return self.change_key(**kwargs)


class BruntClientAsync(BaseClient):
    """Class for the Brunt API."""

    def __init__(
        self,
        username: str = None,
        password: str = None,
        session: ClientSession = None,
    ):
        """Construct for the API wrapper.

        If you supply username and password here, they are stored, but not used.
        Auto logging in then does work when calling another method, no explicit login needed.

        :param username: the username of your Brunt account
        :param password: the password of your Brunt account
        :parm session: aiohttp ClientSession
        """
        super().__init__(username, password)
        self._http = BruntHttpAsync(session=session)

    async def __aenter__(self) -> BruntClientAsync:
        """Enter the context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Exit the context manager."""
        await self.async_close()

    async def async_close(self) -> None:
        """Close the session."""
        await self._http._session.close()

    async def async_login(self, username: str = None, password: str = None) -> bool:
        """Login method using username and password.

        :param username: the username of your Brunt account
        :param password: the password of your Brunt account
        :return: True if successfull
        :raises: errors from Requests call
        """
        await self._http.async_request(
            self._prepare_login(username, password), RequestTypes.POST
        )
        self._lastlogin = datetime.utcnow()
        return True

    async def async_get_things(self, force: bool = False) -> list:
        """Get the things registered in your account.

        :param force: force a refresh from the server, otherwise get from variable.
        :return: list with things registered in the logged in account and API call status
        """
        if not self._things or force:
            return await self._async_get_things()
        return self._things

    async def _async_get_things(self) -> list:
        """Check if there are things in memory, otherwise first do the getThings call and then return _things."""
        if not self._http.is_logged_in:
            await self.async_login()
        resp = await self._http.async_request(MAIN_THINGS_PATH, RequestTypes.GET)
        self._things = resp["things"]
        return self._things

    async def async_get_state(self, **kwargs) -> dict:
        """Get the state of a thing.

        :param thing: a string with the name of the thing, which is then checked using getThings.
        :param thingUri: Uri (string) of the thing you are getting the state from, not checked against getThings.
        :return: a dict with the state of the Thing.
        :raises: ValueError if the requested thing does not exists. NameError if not logged in. SyntaxError when
            not exactly one of the params is given.
        """
        if not self._http.is_logged_in:
            await self.async_login()
        await self._async_get_things()
        return await self._http.async_request(
            self._prepare_state(**kwargs), RequestTypes.GET
        )

    async def async_change_key(self, **kwargs) -> dict:
        """Change a variable of the thing.  Mostly included for future additions.

        :param key: The value you want to change
        :param value: The new value
        :param thing: a string with the name of the thing, which is then checked using getThings.
        :param thingUri: Uri (string) of the thing you are getting the state from, not checked against getThings.
        :return: a dict with the state of the Thing.
        :raises: ValueError if the requested thing does not exists or the position is not between 0 and 100.
            NameError if not logged in. SyntaxError when not exactly one of the params is given.
        """
        if not self._http.is_logged_in:
            await self.async_login()
        await self._async_get_things()
        return await self._http.async_request(
            self._prepare_change_key(**kwargs), RequestTypes.PUT
        )

    async def async_change_request_position(self, request_position, **kwargs) -> dict:
        """Change the position of the thing.

        :param request_position: The new position for the slide (0-100)
        :param thing: a string with the name of the thing, which is then checked using getThings.
        :param thingUri: Uri (string) of the thing you are getting the state from, not checked against getThings.
        :return: a dict with the state of the Thing.
        :raises: ValueError if the requested thing does not exists or the position is not between 0 and 100.
            NameError if not logged in. SyntaxError when not exactly one of the params is given.
        """
        kwargs["key"] = REQUEST_POSITION_KEY
        kwargs["value"] = request_position
        return await self.async_change_key(**kwargs)
