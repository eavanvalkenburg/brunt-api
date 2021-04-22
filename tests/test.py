"""Test script."""
import asyncio
import logging
from aiohttp import ClientSession
import json
from datetime import datetime
import time

from brunt import BruntClientAsync

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


async def main():
    """Run Main Test method."""
    creds = json.loads(open("tests//creds.json").read())
    bapi = BruntClientAsync(
        username=creds["username"], password=creds["password"], session=ClientSession()
    )
    print("Calling Brunt")
    try:
        await bapi.async_login()
        things = await bapi.async_get_things()
        print(things)
        print("")
        move = False
        state = await bapi.async_get_state(thingUri=creds["device"])
        state = state["thing"]
        # things = state['thing']
        print(state)
        print(
            f"    Current status of { state['NAME'] } is position { state['currentPosition'] }"
        )
        if move:
            newPos = 90
            if int(state["currentPosition"]) == 89:
                newPos = 100
            print(f"    Setting { state['NAME'] } to position { newPos }")
            res = await bapi.async_change_request_position(
                newPos, thingUri=creds["device"]
            )
            print(res)
            print("    Success!" if res else "    Fail!")
    except Exception as e:
        await bapi.close()
        print(f"Error: {e}")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
