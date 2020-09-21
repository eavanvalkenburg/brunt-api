"""Test script."""
import asyncio
import brunt

# from brunt.brunt import BruntAPI
import json
from datetime import datetime
import time


async def main():
    """Run Main Test method."""
    creds = json.loads(open("creds.json").read())
    bapi = brunt.BruntAPI(username=creds["username"], password=creds["password"])
    print("Calling Brunt")
    try:
        # await bapi.login()

        print("")
        move = False
        state = await bapi.getState(thingUri=creds["device"])
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
            res = await bapi.changeRequestPosition(newPos, thingUri=creds["device"])
            print(res)
            print("    Success!" if res else "    Fail!")
    except Exception as e:
        await bapi.close()
        print(f"Error: {e}")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
