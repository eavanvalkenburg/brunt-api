# Brunt
Unofficial python SDK for Brunt, based on the npm version here https://github.com/MattJeanes/brunt-api

This package allows you to control your Brunt devices from code.

## Methods
There are four methods:
1. login
    * requires username and password
    * this method always needs to be called at the start of a session because it pulls in a sessionid from the server
    * returns True when completed
1. getThings
    * no parameters
    * returns the response body as a json dict from the Brunt server, which has details about all your things
1. getState
    * name of the thing
    * returns the details of the state as a json dict from the Brunt server
1. changePosition
    * name of the thing and the requested position
    * returns True if the return status code was 200 (success)

## Sample script

This script shows the usage and how to use the output of the calls, off course if you already know the name of your device you do not need to call getThings.

This script checks the current position of a blind called 'Blind' and if that is 100 (fully open), sets it to 90 and vice versa.

```python
from brunt.brunt import BruntAPI

bapi = BruntAPI()
print("Calling Brunt")

bapi.login('username', 'password')
print("    Logged in, gettings things.")

things = bapi.getThings()
print(f"    { len(things) } thing(s) found.")

state = bapi.getState('Blind')
print(f"    Current status of { state['NAME'] } is position { state['currentPosition'] }")
newPos = 100
if int(state['currentPosition']) == 100:
    newPos = 90
print(f"    Setting { state['NAME'] } to position { newPos }")

res = bapi.changePosition('Blind', newPos)
print('    Success!' if res else '    Fail!')
    
```