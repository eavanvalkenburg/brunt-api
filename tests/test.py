"""Test script."""
import asyncio
import logging
from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientResponseError
import json
from datetime import datetime
import time

from brunt import BruntClientAsync, Thing


logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)


async def main():
    """Run Main Test method."""
    creds = json.loads(open("tests//creds.json").read())
    bapi = BruntClientAsync(username=creds["username"], password=creds["password"])
    print("Calling Brunt")
    # try:
    await bapi.async_login()
    try:
        print(bapi.last_requested_positions)
    except ValueError:
        print("No positions yet.")
    things = await bapi.async_get_things()
    print(f"things: {things}")
    # try:
    #     print(bapi.last_requested_positions)
    # except ValueError:
    #     print("No positions yet.")
    state = await bapi.async_get_state(thing="Blind")
    print(f"state: {state}")
    print(
        f"    Current status of { state.name } is position { state.current_position }"
    )
    move = True
    if move:
        newPos = 99
        if state.request_position == 99:
            newPos = 100
        print(f"    Setting { state.name } to position { newPos }")
        await bapi.async_change_request_position(thing="Blind", request_position=newPos)
    # try:
    #     print(bapi.last_requested_positions)
    # except ValueError:
    #     print("No positions yet.")
    # except Exception as e:
    #     print(f"Error: {e}")
    # finally:
    await bapi.async_close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
