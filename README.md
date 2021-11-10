[![PyPI version](https://badge.fury.io/py/brunt.svg)](https://badge.fury.io/py/brunt)

# Brunt
Unofficial python SDK for Brunt, based on the NPM version here https://github.com/MattJeanes/brunt-api

This package allows you to control your Brunt devices from code.

## Sample script

This script shows the usage and how to use the output of the calls, off course if you already know the name of your device you do not need to call getThings.

This script checks the current position of a blind called 'Blind' and if that is 100 (fully open), sets it to 90 and vice versa.

```python
from brunt import BruntClient, BruntClientAsync

bapi = BruntClient() 
# bapi = BruntClientAsync()
print("Calling Brunt")

bapi.login('username', 'password')
# await bapi.async_login('username', 'password')
print("    Logged in, gettings things.")

things = bapi.get_things()['things']
# things = await bapi.async_get_things()['things']
print(f"    { len(things) } thing(s) found.")

state = bapi.get_state(thing='Blind')['thing']
# state = await bapi.async_get_state(thing='Blind')['thing']
print(f"    Current status of { state['NAME'] } is position { state['currentPosition'] }")
newPos = 100
if int(state['currentPosition']) == 100:
    newPos = 90
print(f"    Setting { state['NAME'] } to position { newPos }")

res = bapi.change_request_position(newPos, thing='Blind')
# res = await bapi.async_change_request_position(newPos, thing='Blind')
print('    Success!' if res else '    Fail!')
    
```
<h1 id="brunt.BruntClient">BruntClient & BruntClientAsync</h1>

```python
from brunt import BruntClient
BruntClient(username, password)

or 

from brunt import BruntClientAsync
BruntClientAsync(username, password, session)
```
Constructor for the API wrapper.

If you supply username and password here, they are stored, but not used.
Auto logging in then does work when calling another method, no explicit login needed.

:param username: the username of your Brunt account
:param password: the password of your Brunt account

Async only :param session: aiohttp.ClientSession object

<h2 id="brunt.BruntClient.login">login</h2>

```python
BruntClient.login(self, username, password)
await BruntClient.async_login(self, username, password)
```
Login method using username and password

:param username: the username of your Brunt account
:param password: the password of your Brunt account

:return: True if successful
:raises: errors from Requests call

<h2 id="brunt.brunt.BruntClient.getThings">get_things</h2>

```python
BruntClient.get_things(self)
await BruntClient.async_get_things(self)
```
Get the things registered in your account

:return: List of Things
:raises: errors from Requests call

<h2 id="brunt.brunt.BruntClient.getState">get_state</h2>

```python
BruntClient.get_state(self, thing="Blind")
await BruntClient.async_get_state(self, thing="Blind")
```
Get the state of a thing, by NAME or thingUri

:param thing: a string with the NAME of the thing, which is then checked against the names of all the things.
:param thingUri: Uri (string) of the thing you are getting the state from, not checked against getThings.

:return: a Thing.
:raises: ValueError if the requested thing does not exists. NameError if not logged in. SyntaxError when
    not exactly one of the params is given.

<h2 id="brunt.brunt.BruntClient.changeRequestPosition">change_request_position</h2>

```python
BruntClient.change_request_position(self, request_position, thing="Blind")
await BruntClient.async_change_request_position(self, request_position, thing="Blind")
```
Changes the position of the thing. Internally calls the changeKey method with key set to
requestPosition and value set to request_position

:param request_position: The new position for the slide (0-100)
:param thing: a string with the name of the thing, which is then checked against the names of all the things.
:param thingUri: Uri (string) of the thing you are getting the state from, not checked against getThings.

:return: a dict with 'result'.
:raises: ValueError if the requested thing does not exists or the position is not between 0 and 100.
    NameError if not logged in. SyntaxError when not exactly one of the params is given.

<h2 id="brunt.brunt.BruntClient.changeKey">change_key</h2>

```python
BruntClient.change_key(self, key="requestPosition", value="100", thing="Blind")
await BruntClient.async_change_key(self, key="requestPosition", value="100", thing="Blind")
```
Change a variable of the thing by supplying the key and value. Mostly included for future additions.

:param key: The key of the value you want to change
:param value: The new value
:param thing: a string with the name of the thing, which is then checked using getThings.
:param thingUri: Uri (string) of the thing you are getting the state from, not checked against getThings.
:return: a dict with 'result'.
:raises: ValueError if the requested thing does not exists or the position is not between 0 and 100. 
    NameError if not logged in. SyntaxError when not exactly one of the params is given. 
