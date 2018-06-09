
from requests import Request, Session
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

    def request(self, session, data, request_type: RequestTypes):
        """ internal request method 
        
        :param session: session object from the Requests package
        :param data: internal data of your API call
        :param request: the type of request, based on the RequestType enum
        :returns: dict with sessionid for a login and the dict of the things for the other calls, or just success for PUT
        :raises: raises errors from Requests through the raise_for_status function
        """
        #prepare the URL to send the request to
        url = f"{ data['host'] }{ data['path'] }"
        #fixed header content
        headers = self._DEFAULT_HEADER

        #prepare the payload and add the length to the header, payload might be empty.
        if "data" in data:
            payload = json.dumps(data['data'])
            headers["Content-Length"] = str(len(data['data']))
        else: payload = ""
        #prepare the request and add it to the session
        req = Request(request_type.value, url,  data=payload, headers=headers)
        prepped = session.prepare_request(req)
        #send the request
        resp = session.send(prepped)#, timeout=20)
        # raise an error if it occured in the Request.
        resp.raise_for_status()
        # no error, so set result to success
        ret = {'result': 'success'}
        # check if there is something in the response body
        if len(resp.json()) > 0: 
            # if it is a list of things, then set the tag to things
            if type(resp.json()) is list:
                ret['things'] = resp.json()
            # otherwise to a single thing.
            else:                
                ret['thing'] = resp.json()
        # if the response had a cookie with that key, add that to the session object
        if 'skySSEIONID' in resp.cookies:
            session.cookies = resp.cookies     
        return ret

class BruntAPI:
    def __init__(self):
        """ """
        self._http = BruntHttp()
        self._things = {}
        self._s = Session()

    def login(self, username, password):
        """ Login method using username and password
        
        :param username: the username of your Brunt account
        :param password: the password of your Brunt account
        :return: True if successfull
        :raises: errors from Requests call
        """
        data = {
            "data": {
                "ID": username,
                "PASS": password,
            },
            "path": "/session",
            "host": "https://sky.brunt.co"
        }
        return self._http.request(self._s, data, RequestTypes.POST)

    def _is_logged_in(self):
        """ Check whether or not the user is logged in. """        
        return True if self._s.cookies else False 

    def getThings(self):
        """ Get the things registered in your account 
        
        :return: dict with things registered in the logged in account and API call status
        """
        if not self._is_logged_in():
            raise NameError("Please login first using the login function, with username and password")
        data = {
            "path": "/thing",
            "host": "https://sky.brunt.co"
        }
        resp = self._http.request(self._s, data, RequestTypes.GET)
        self._things = resp['things']
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
        if not self._is_logged_in():
            raise NameError("Please login first using the login function, with username and password")
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
                        raise ValueError(f'Unknown thing: { thing }.')
                else:
                    raise ValueError('No things available.')
        else:
            return SyntaxError("Please provide either the 'thing' name or the 'thingUri' not both and at least one")
        data = {
            "path": "/thing" + thingUri,
            "host": "https://thing.brunt.co:8080" 
        }
        return self._http.request(self._s, data, RequestTypes.GET)

    def changePosition(self, position, **kwargs):
        """Change the position of the thing.

        :param position: The new position for the slide (0-100)
        :param thing: a string with the name of the thing, which is then checked using getThings.
        :param thingUri: Uri (string) of the thing you are getting the state from, not checked against getThings.
        :return: a dict with the state of the Thing.
        :raises: ValueError if the requested thing does not exists or the position is not between 0 and 100. 
            NameError if not logged in. SyntaxError when not exactly one of the params is given. 
        """
        if not self._is_logged_in():
            raise NameError("Please login first using the login function, with username and password")
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
                        raise ValueError(f'Unknown thing: { thing }.')
                else:
                    raise ValueError('No things available.')
        else:
            return SyntaxError("Please provide either the 'thing' name or the 'thingUri' not both and at least one")

        # check validity of the position
        if position < 0 or position > 100:
            return ValueError("Please set the position between 0 and 100.")

        #prepare data payload
        data = {
            "data": {
                "requestPosition": str(position)
            },
            "path": "/thing" + thingUri,
            "host": "https://thing.brunt.co:8080"
        }
        #call the request method and return the response.
        return self._http.request(self._s, data, RequestTypes.PUT)

