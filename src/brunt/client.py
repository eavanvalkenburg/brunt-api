"""Main code for brunt api package."""
from __future__ import annotations

from abc import ABC
from datetime import datetime, timedelta
import logging
from types import TracebackType
from typing import List, Optional, Type

from .const import MAIN_HOST, MAIN_THINGS_PATH, REQUEST_POSITION_KEY, THINGS_HOST
from .http import BruntHttp, BruntHttpAsync
from .utils import RequestTypes

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


class BaseClient(ABC):
    """Base class for clients."""

    def __init__(self, **kwargs):
        """Construct for the API wrapper.

        If you supply username and password here, they are stored, but not used.
        Auto logging in then does work when calling another method, no explicit login needed.

        :param username: the username of your Brunt account
        :param password: the password of your Brunt account
        """
        self._user: str = kwargs.get("username", "")
        self._pass: str = kwargs.get("password", "")
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

    @property
    def _relogin(self) -> bool:
        """Return whether a relogin is necessary."""
        if not self._lastlogin:
            return True
        return datetime.utcnow() >= (self._lastlogin + timedelta(hours=24))


class BruntClient(BaseClient):
    """Class for the Brunt API."""

    def __init__(self, **kwargs):
        """Construct for the API wrapper.

        If you supply username and password here, they are stored, but not used.
        Auto logging in then does work when calling another method, no explicit login needed.

        :param username: the username of your Brunt account
        :param password: the password of your Brunt account
        """
        super().__init__(**kwargs)
        self._http = BruntHttp()

    def login(self, username: str = None, password: str = None) -> dict:
        """Login method using username and password.

        :param username: the username of your Brunt account
        :param password: the password of your Brunt account
        :return: True if successfull
        :raises: errors from Requests call
        """
        resp = self._http.request(
            self._prepare_login(username, password), RequestTypes.POST
        )
        self._lastlogin = datetime.utcnow()
        return resp

    def _is_logged_in(self) -> dict:
        """Check whether or not the user is logged in."""
        if self._relogin:
            return self.login()
        return {}

    def get_things(self) -> dict:
        """Get the things registered in your account.

        :return: dict with things registered in the logged in account and API call status
        """
        login_return = self._is_logged_in()
        resp = self._http.request(MAIN_THINGS_PATH, RequestTypes.GET)
        self._things = resp["things"]
        resp.update(login_return)
        return resp

    def _get_things(self) -> list:
        """Check if there are things in memory, otherwise first do the getThings call and then return _things.

        :return: dict with things registered (without API call status)
        """
        if not self._things:
            self.get_things()
        return self._things

    def get_state(self, **kwargs) -> dict:
        """Get the state of a thing.

        :param thing: a string with the name of the thing, which is then checked using getThings.
        :param thingUri: Uri (string) of the thing you are getting the state from, not checked against getThings.
        :return: a dict with the state of the Thing.
        :raises: ValueError if the requested thing does not exists. NameError if not logged in. SyntaxError when
            not exactly one of the params is given.
        """
        self._get_things()
        login_return = self._is_logged_in()
        resp = self._http.request(self._prepare_state(**kwargs), RequestTypes.GET)
        resp.update(login_return)
        return resp

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
        self._get_things()
        login_return = self._is_logged_in()
        resp = self._http.request(self._prepare_change_key(**kwargs), RequestTypes.PUT)
        resp.update(login_return)
        return resp

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

    def __init__(self, **kwargs):
        """Construct for the API wrapper.

        If you supply username and password here, they are stored, but not used.
        Auto logging in then does work when calling another method, no explicit login needed.

        :param username: the username of your Brunt account
        :param password: the password of your Brunt account
        :parm session: aiohttp ClientSession
        """
        super().__init__(**kwargs)
        self._http = BruntHttpAsync(kwargs.get("session"))

    async def __aenter__(self) -> BruntClientAsync:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the session."""
        await self._http._session.close()

    async def async_login(self, username: str = None, password: str = None) -> dict:
        """Login method using username and password.

        :param username: the username of your Brunt account
        :param password: the password of your Brunt account
        :return: True if successfull
        :raises: errors from Requests call
        """
        resp = await self._http.async_request(
            self._prepare_login(username, password), RequestTypes.POST
        )
        self._lastlogin = datetime.utcnow()
        return resp

    async def _async_is_logged_in(self) -> dict:
        """Check whether or not the user is logged in."""
        # if the user has not logged in in 24 hours, relogin
        if self._relogin:
            return await self.async_login()
        return {}

    async def async_get_things(self) -> dict:
        """Get the things registered in your account.

        :return: dict with things registered in the logged in account and API call status
        """
        login_return = await self._async_is_logged_in()
        resp = await self._http.async_request(MAIN_THINGS_PATH, RequestTypes.GET)
        self._things = resp["things"]
        resp.update(login_return)
        return resp

    async def _async_get_things(self) -> list:
        """Check if there are things in memory, otherwise first do the getThings call and then return _things.

        :return: dict with things registered (without API call status)
        """
        if not self._things:
            await self.async_get_things()
        return self._things

    async def async_get_state(self, **kwargs) -> dict:
        """Get the state of a thing.

        :param thing: a string with the name of the thing, which is then checked using getThings.
        :param thingUri: Uri (string) of the thing you are getting the state from, not checked against getThings.
        :return: a dict with the state of the Thing.
        :raises: ValueError if the requested thing does not exists. NameError if not logged in. SyntaxError when
            not exactly one of the params is given.
        """
        await self._async_get_things()
        login_return = await self._async_is_logged_in()
        resp = await self._http.async_request(
            self._prepare_state(**kwargs), RequestTypes.GET
        )
        resp.update(login_return)
        return resp

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
        await self._async_get_things()
        login_return = await self._async_is_logged_in()
        resp = await self._http.async_request(
            self._prepare_change_key(**kwargs), RequestTypes.PUT
        )
        resp.update(login_return)
        return resp

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
