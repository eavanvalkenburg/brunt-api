"""Main code for brunt api package."""
from __future__ import annotations

import logging
from datetime import datetime
from types import TracebackType
from typing import Any, List, Optional, Type, Union

from aiohttp.client import ClientSession
from requests import Session

from .const import MAIN_HOST, MAIN_THINGS_PATH, REQUEST_POSITION_KEY, THINGS_HOST
from .http import BruntHttp, BruntHttpAsync
from .thing import Thing
from .utils import RequestTypes

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


class BaseClient:
    """Base class for clients."""

    def __init__(self, username: str = None, password: str = None):
        """Construct for the API wrapper.

        If you supply username and password here, they are stored, but not used.
        Auto logging in then does work when calling another method,
            no explicit login needed.

        :param username: the username of your Brunt account
        :param password: the password of your Brunt account
        """
        self._user: str | None = username
        self._pass: str | None = password
        self._things: List[Thing] | None = None
        self._last_login: datetime | None = None
        self._last_requested_position: dict[str, int] | None = None

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

    def _prepare_state(self, thing: str = None, thing_uri: str = None) -> dict:
        """Prepare the data for a Get State call."""
        if thing is None and thing_uri is None:
            raise SyntaxError(
                "Please provide either the 'thing' name or the 'thing_uri', \
                    the thing_uri is used first when given."
            )
        if thing_uri is None and thing is not None:
            thing_uri = self._get_thing_uri_from_thing(thing)
        return {"path": f"/thing{thing_uri}", "host": THINGS_HOST}

    def _prepare_change_key(
        self, key: str, value: Any, thing: str = None, thing_uri: str = None
    ) -> dict:
        """Prepare the data for the change key call."""
        if thing is None and thing_uri is None:
            raise SyntaxError(
                "Please provide either the 'thing' name or the 'thing_uri',\
                     the thing_uri is used first when given."
            )
        if thing_uri is None and thing is not None:
            thing_uri = self._get_thing_uri_from_thing(thing)
        if key == REQUEST_POSITION_KEY:
            if int(value) < 0 or int(value) > 100:
                raise ValueError("Please set the position between 0 and 100.")
            if thing_uri:
                if self._last_requested_position is not None:
                    self._last_requested_position[thing_uri] = int(value)
                else:
                    self._last_requested_position = {thing_uri: int(value)}
        return {
            "data": {key: str(value)},
            "path": f"/thing{thing_uri}",
            "host": THINGS_HOST,
        }

    def _get_thing_uri_from_thing(self, thing: str) -> str:
        """Get the thing_uri for a thing."""
        if self._things is None:
            raise ValueError("Refresh things first")
        thing_uri = next(
            (t.thing_uri for t in self._things if t.compare_name(thing)), None
        )
        if thing_uri is None:
            raise ValueError("Unknown thing: " + thing)
        return thing_uri

    @property
    def last_requested_positions(self) -> dict[str, int]:
        """Return the last requested positions."""
        if self._things is None:
            raise ValueError("Refresh things first")
        ret = {
            t.thing_uri: int(t.request_position)
            for t in self._things
            if t.thing_uri is not None
        }
        if self._last_requested_position is not None:
            ret.update(self._last_requested_position)
        return ret


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
        Auto logging in then does work when calling another method,
            no explicit login needed.

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
        self._http.session.close()

    def login(self, username: str = None, password: str = None) -> bool:
        """Login method using username and password.

        :param username: the username of your Brunt account
        :param password: the password of your Brunt account
        :return: True if successfull
        :raises: errors from Requests call
        """
        self._http.request(self._prepare_login(username, password), RequestTypes.POST)
        self._last_login = datetime.utcnow()
        return True

    def get_things(self, force: bool = False) -> List[Thing]:
        """Get all the things.

        Check if there are things in memory. otherwise first do the getThings call
        and then return _things.

        :return: dict with things registered (without API call status)
        """
        if not self._things or force:
            return self._get_things()
        return self._things

    def _get_things(self) -> List[Thing]:
        """Get the things registered in your account.

        :return: dict with things registered in the logged in account
            and API call status
        """
        if not self._http.is_logged_in:
            self.login()
        resp = self._http.request(MAIN_THINGS_PATH, RequestTypes.GET)
        if isinstance(resp, list):
            self._things = [Thing.create_from_dict(r) for r in resp]
            return self._things
        return []

    def get_state(self, thing: str = None, thing_uri: str = None) -> Thing:
        """Get the state of a thing.

        :param thing: a string with the name of the thing, which is then
            checked using getThings.
        :param thing_uri: Uri (string) of the thing you are getting the state from,
            not checked against getThings.
        :return: a dict with the state of the Thing.
        :raises: ValueError if the requested thing does not exists.
            NameError if not logged in.
            SyntaxError when not exactly one of the params is given.
        """
        if not self._http.is_logged_in:
            self.login()
        self.get_things()
        resp = self._http.request(
            self._prepare_state(thing=thing, thing_uri=thing_uri), RequestTypes.GET
        )
        return Thing.create_from_dict(resp)  # type: ignore

    def change_key(
        self, key: str, value: Any, thing: str = None, thing_uri: str = None
    ) -> Union[dict, list]:
        """Change a variable of the thing.  Mostly included for future additions.

        :param key: The value you want to change
        :param value: The new value
        :param thing: a string with the name of the thing, which is then
            checked using getThings.
        :param thing_uri: Uri (string) of the thing you are getting the state from,
            not checked against getThings.
        :return: a dict with the state of the Thing.
        :raises: ValueError if the requested thing does not exists or the position is
            not between 0 and 100.
            NameError if not logged in.
            SyntaxError when not exactly one of the params is given.
        """
        if not self._http.is_logged_in:
            self.login()
        self.get_things()
        return self._http.request(
            self._prepare_change_key(
                key=key, value=value, thing=thing, thing_uri=thing_uri
            ),
            RequestTypes.PUT,
        )

    def change_request_position(
        self, request_position: int, thing: str = None, thing_uri: str = None
    ) -> Union[dict, list]:
        """Change the position of the thing.

        :param request_position: The new position for the slide (0-100)
        :param thing: a string with the name of the thing, which is then checked
            using getThings.
        :param thing_uri: Uri (string) of the thing you are getting the state from,
            not checked against getThings.
        :return: a dict with the state of the Thing.
        :raises: ValueError if the requested thing does not exists or the position
            is not between 0 and 100.
            NameError if not logged in. SyntaxError when not exactly one of the params
                is given.
        """
        return self.change_key(
            key=REQUEST_POSITION_KEY,
            value=request_position,
            thing=thing,
            thing_uri=thing_uri,
        )


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
        Auto logging in then does work when calling another method,
            no explicit login needed.

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
        await self._http.session.close()

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
        self._last_login = datetime.utcnow()
        return True

    async def async_get_things(self, force: bool = False) -> List[Thing]:
        """Get the things registered in your account.

        :param force: force a refresh from the server, otherwise get from variable.
        :return: list with things registered in the logged in account and API call status
        """
        if not self._things or force:
            return await self._async_get_things()
        return self._things

    async def _async_get_things(self) -> List[Thing]:
        """Get the things.

        Check if there are things in memory, otherwise first do the getThings call and
        then return _things.
        """
        if not self._http.is_logged_in:
            await self.async_login()
        resp = await self._http.async_request(MAIN_THINGS_PATH, RequestTypes.GET)
        if isinstance(resp, list):
            self._things = [Thing.create_from_dict(r) for r in resp]
            return self._things
        return []

    async def async_get_state(self, thing: str = None, thing_uri: str = None) -> Thing:
        """Get the state of a thing.

        :param thing: a string with the name of the thing, which is then checked
            using getThings.
        :param thing_uri: Uri (string) of the thing you are getting the state from,
            not checked against getThings.
        :return: a dict with the state of the Thing.
        :raises: ValueError if the requested thing does not exists.
            NameError if not logged in. SyntaxError when
            not exactly one of the params is given.
        """
        if not self._http.is_logged_in:
            await self.async_login()
        await self.async_get_things()
        resp = await self._http.async_request(
            self._prepare_state(thing=thing, thing_uri=thing_uri), RequestTypes.GET
        )
        return Thing.create_from_dict(resp)  # type: ignore

    async def async_change_key(
        self, key: str, value: Any, thing: str = None, thing_uri: str = None
    ) -> Union[dict, list]:
        """Change a variable of the thing.  Mostly included for future additions.

        :param key: The value you want to change
        :param value: The new value
        :param thing: a string with the name of the thing, which is then checked
            using getThings.
        :param thing_uri: Uri (string) of the thing you are getting the state from,
            not checked against getThings.
        :return: a dict with the state of the Thing.
        :raises: ValueError if the requested thing does not exists or the position is
            not between 0 and 100.
            NameError if not logged in. SyntaxError when not exactly one of
                the params is given.
        """
        if not self._http.is_logged_in:
            await self.async_login()
        await self.async_get_things()
        return await self._http.async_request(
            self._prepare_change_key(
                key=key, value=value, thing=thing, thing_uri=thing_uri
            ),
            RequestTypes.PUT,
        )

    async def async_change_request_position(
        self, request_position: int, thing: str = None, thing_uri: str = None
    ) -> Union[dict, list]:
        """Change the position of the thing.

        :param request_position: The new position for the slide (0-100)
        :param thing: a string with the name of the thing, which is then checked
            using getThings.
        :param thing_uri: Uri (string) of the thing you are getting the state from,
            not checked against getThings.
        :return: a dict with the state of the Thing.
        :raises: ValueError if the requested thing does not exists or the position
            is not between 0 and 100.
            NameError if not logged in. SyntaxError when not exactly one of the
                params is given.
        """
        return await self.async_change_key(
            key=REQUEST_POSITION_KEY,
            value=request_position,
            thing=thing,
            thing_uri=thing_uri,
        )
