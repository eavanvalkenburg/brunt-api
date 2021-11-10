"""Test script."""
import asyncio
import logging
from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientResponseError
import json
from datetime import datetime
import time

from brunt import BruntClientAsync, Thing
from brunt.utils import RequestTypes

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)


async def main():
    """Run Main Test method."""
    creds = json.loads(open("tests//creds.json").read())
    # cases = [None, "password", "username", "both", "thingUri"]
    cases = ["thingUri"]
    for case in cases:
        username = creds["username"]
        password = creds["password"]
        bapi = BruntClientAsync(
            username="failname" if case in ["username", "both"] else username,
            password="failpass" if case in ["password", "both"] else password,
        )
        print("Calling Brunt")
        try:
            await bapi.async_login()
            if case == "thingUri":
                things = await bapi.async_get_things()
                _LOGGER.debug("Things: %s", things)
                _LOGGER.debug("ThingUri: %s", things[0].thingUri)
                await bapi._http.async_request(
                    bapi._prepare_state(thingUri="/hub/1234567890"), RequestTypes.GET
                )
        except Exception as exp:
            _LOGGER.error("Caught error: %s", exp)
        finally:
            await bapi.async_close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
