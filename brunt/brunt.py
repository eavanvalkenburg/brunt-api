
import requests
from datetime import datetime, timedelta
from enum import Enum
import json

class RequestTypes(Enum):
    POST = 'POST'
    GET = 'GET'
    PUT = 'PUT'

class BruntHttp:
    _DEFAULT_HEADER = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://sky.brunt.co",
            "Accept-Language": "en-gb",
            "Accept": "application/vnd.brunt.v1+json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E216"
            }

    def __init__(self):
        """ """
        self._sessionid = ''

    def _has_session(self):
        """ Check whether or not the user is logged in. """
        return True if self._sessionid else False

    def request(self, data, request_type: RequestTypes):
        """ internal request method 
        
        :param session: session object from the Requests package
        :param data: internal data of your API call
        :param request: the type of request, based on the RequestType enum
        :returns: dict with sessionid for a login and the dict of the things for the other calls, or just success for PUT
        :raises: raises errors from Requests through the raise_for_status function
        """
        #prepare the URL to send the request to
        url = data['host'] + data['path']

        #fixed header content
        headers = self._DEFAULT_HEADER
        if self._sessionid:
            headers['Cookie'] = "skySSEIONID=" + self._sessionid

        #prepare the payload and add the length to the header, payload might be empty.
        if "data" in data:
            payload = json.dumps(data['data'])
            headers["Content-Length"] = str(len(data['data']))
        else: payload = ""
        
        #send the request and capture the response
        resp = requests.request(request_type.value, url, data=payload, headers=headers)
        # raise an error if it occured in the Request.
        resp.raise_for_status()
        # no error, so set result to success
        ret = {'result': 'success'}
        # check if there is something in the response body
        if len(resp.text) > 0:
            respjson = resp.json()
            # if it is a list of things, then set the tag to things
            if type(respjson) is list:
                ret['things'] = respjson
            # otherwise to a single thing. If ID is part of it it is a login response, otherwise a Thing
            elif "ID" in respjson:
                ret['login'] = respjson
                # if it was a login a new cookie was send back, capture the sessionid from it
                self._sessionid = resp.cookies['skySSEIONID']
                ret['cookie'] = resp.cookies
            else:            
                ret['thing'] = respjson
        return ret

class BruntAPI:
    def __init__(self, **kwargs):
        """ Constructor for the API wrapper.
        
        If you supply username and password here, they are stored, but not used.
        Auto logging in then does work when calling another method, no explicit login needed.

        :param username: the username of your Brunt account
        :param password: the password of your Brunt account
        """
        self._user = None
        self._pass = None
        if 'username' in kwargs:
            self._user = kwargs['username']
        if 'password' in kwargs:
            self._pass = kwargs['password']
        self._http = BruntHttp()
        self._things = {}
        self._lastlogin = None

    def login(self, username, password):
        """ Login method using username and password
        
        :param username: the username of your Brunt account
        :param password: the password of your Brunt account
        :return: True if successfull
        :raises: errors from Requests call
        """
        self._user = username
        self._pass = password
        return self._login()
    
    def _login(self):
        if not self._user or not self._pass:
            raise NameError("Please login first using the login function, with username and password")
        data = {
            "data": {
                "ID": self._user,
                "PASS": self._pass,
            },
            "path": "/session",
            "host": "https://sky.brunt.co"
        }
        resp = self._http.request(data, RequestTypes.POST)
        self._lastlogin = datetime.utcnow()
        return resp

    def _is_logged_in(self):
        """ Check whether or not the user is logged in. """
        # if the user has not logged in in 24 hours, relogin
        if not self._http._has_session() or datetime.utcnow() >= self._lastlogin + timedelta(hours=24):
            return self._login()
        else:
            return {}

    def getThings(self):
        """ Get the things registered in your account 
        
        :return: dict with things registered in the logged in account and API call status
        """
        login_return = self._is_logged_in()
            # raise NameError("Please login first using the login function, with username and password")
        data = {
            "path": "/thing",
            "host": "https://sky.brunt.co"
        }
        resp = self._http.request(data, RequestTypes.GET)
        self._things = resp['things']
        resp.update(login_return)
        return resp

    def _getThings(self):
        """ check if there are things in memory, otherwise first do the getThings call and then return _things 
        
        :return: dict with things registered (without API call status)
        """
        if not self._things:
            self.getThings()
        return self._things

    def getState(self, **kwargs):
        """Get the state of a thing

        :param thing: a string with the name of the thing, which is then checked using getThings.
        :param thingUri: Uri (string) of the thing you are getting the state from, not checked against getThings.
        :return: a dict with the state of the Thing.
        :raises: ValueError if the requested thing does not exists. NameError if not logged in. SyntaxError when 
            not exactly one of the params is given.
        """
        login_return = self._is_logged_in()
        if "thingUri" in kwargs:
            thingUri = kwargs['thingUri']
        elif "thing" in kwargs:
            thing = kwargs['thing']
            for t in self._getThings():
                if 'NAME' in t:
                    if  t['NAME'] == thing and 'thingUri' in t:
                        thingUri = t['thingUri']
                        break
                    else:
                        raise ValueError('Unknown thing: ' + thing)
                else:
                    raise ValueError('No things available.')
        else:
            return SyntaxError("Please provide either the 'thing' name or the 'thingUri' not both and at least one")
        data = {
            "path": "/thing" + thingUri,
            "host": "https://thing.brunt.co:8080" 
        }
        resp = self._http.request(data, RequestTypes.GET)
        resp.update(login_return)
        return resp

    def changeKey(self, **kwargs):
        """Change a variable of the thing.  Mostly included for future additions.

        :param key: The value you want to change
        :param value: The new value
        :param thing: a string with the name of the thing, which is then checked using getThings.
        :param thingUri: Uri (string) of the thing you are getting the state from, not checked against getThings.
        :return: a dict with the state of the Thing.
        :raises: ValueError if the requested thing does not exists or the position is not between 0 and 100. 
            NameError if not logged in. SyntaxError when not exactly one of the params is given. 
        """
        login_return = self._is_logged_in()
        #check the thing being changed
        if "thingUri" in kwargs:
            thingUri = kwargs['thingUri']
        elif "thing" in kwargs:
            thing = kwargs['thing']
            for t in self._getThings():
                if 'NAME' in t:
                    if  t['NAME'] == thing and 'thingUri' in t:
                        thingUri = t['thingUri']
                        break
                    else:
                        raise ValueError('Unknown thing: ' + thing)
                else:
                    raise ValueError('No things available.')
        else:
            return SyntaxError("Please provide either the 'thing' name or the 'thingUri' not both and at least one")

        if 'key' in kwargs:
            key = kwargs['key']
        else:
            raise SyntaxError("Please provide a key to change")

        if 'value' in kwargs:
            value = kwargs['value']
        else:
            raise SyntaxError("Please provide a value to change to")

        if key.lower().find('position'):
            if int(value) < 0 or int(value) > 100:
                return ValueError("Please set the position between 0 and 100.")

        #prepare data payload
        data = {
            "data": {
                str(key): str(value)
            },
            "path": "/thing" + thingUri,
            "host": "https://thing.brunt.co:8080"
        }
        
        #call the request method and return the response.
        resp = self._http.request(data, RequestTypes.PUT)
        resp.update(login_return)
        return resp

    def changeRequestPosition(self, request_position, **kwargs):
        """Change the position of the thing.

        :param request_position: The new position for the slide (0-100)
        :param thing: a string with the name of the thing, which is then checked using getThings.
        :param thingUri: Uri (string) of the thing you are getting the state from, not checked against getThings.
        :return: a dict with the state of the Thing.
        :raises: ValueError if the requested thing does not exists or the position is not between 0 and 100. 
            NameError if not logged in. SyntaxError when not exactly one of the params is given. 
        """
        kwargs['key']="requestPosition"
        kwargs['value']=request_position
        return self.changeKey(**kwargs)
