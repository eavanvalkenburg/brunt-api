"""Test script."""
import asyncio
import logging
import json

from brunt import BruntClient


logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)


async def main():
    """Run Main Test method."""
    creds = json.loads(open("tests//creds.json").read())
    bapi = BruntClient(username=creds["username"], password=creds["password"])
    print("Calling Brunt (sync)")
    try:
        bapi.login()
        things = bapi.get_things()
        print(things)
        state = bapi.get_state(thingUri=creds["device"])
        print(
            f"    Current status of { state.NAME } is position { state.currentPosition }"
        )
        move = False
        if move:
            newPos = 90
            if int(state.currentPosition) == 89:
                newPos = 100
            print(f"    Setting { state['NAME'] } to position { newPos }")
            res = bapi.change_request_position(newPos, thingUri=creds["device"])
            print(res)
            print("    Success!" if res else "    Fail!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        bapi.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
