
from requests import Request, Session
import json
from simplejson.scanner import JSONDecodeError
from enum import Enum

class RequestTypes(Enum):
    POST = 'POST'
    GET = 'GET'
    PUT = 'PUT'

class BruntHttp:
    def __init__(self):
        """ init of the https methods """
        self._sessionid = None

    def request(self, s, data, request_type):
        """ request method """
        url = data['host'] + data['path']
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://sky.brunt.co",
            "Accept-Language": "en-gb",
            "Accept": "application/vnd.brunt.v1+json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E216"
            }

        if "sessionId" in data:
            headers["Cookie"] = "skySSEIONID=" + data['sessionId']

        if "data" in data:
            payload = json.dumps(data['data'])
            headers["Content-Length"] = str(len(data['data']))
        else:
            payload = {}

        req = Request(request_type.value, url,  data=payload, headers=headers)
        prepped = s.prepare_request(req)
        resp = s.send(prepped)

        sessionid = None
        if 'skySSEIONID' in resp.cookies:
            sessionid = resp.cookies['skySSEIONID']

        if request_type == RequestTypes.POST:
            ret = sessionid
        elif request_type == RequestTypes.GET:
            ret = resp.json()
        elif request_type == RequestTypes.PUT:
            ret = resp.status_code == 200

        return ret

class BruntAPI:
    def __init__(self):
        """ """
        self._http = BruntHttp()
        self._sessionid = None
        self._things = None
        self._s = Session()

    def login(self, username, password):
        """ Login method """
        data = {
            "data": {
                "ID": username,
                "PASS": password,
            },
            "path": "/session",
            "host": "https://sky.brunt.co"
        }        
        ret = self._http.request(self._s, data, RequestTypes.POST)
        self._sessionid = ret
        return True

    def getThings(self):
        """ Get the things registered in your account """
        data = {
            "path": "/thing",
            "host": "https://sky.brunt.co",
            "sessionId": self._sessionid
        }
        ret = self._http.request(self._s, data, RequestTypes.GET)
        self._things = ret
        return self._things

    def getState(self, thing):
        """ Get the state of a thing by name """
        for t in self._things :
            if 'NAME' in t:
                if  t['NAME'] == thing and 'thingUri' in t:
                    thingUri = t['thingUri']
                    break
                else:
                    raise NameError(f'No thing with the name { thing } present.')
            else:
                raise NameError('No things available.')

        data = {
            "path": "/thing" + thingUri,
            "host": "https://thing.brunt.co:8080",
            "sessionId": self._sessionid
        }
        resp = self._http.request(self._s, data, RequestTypes.GET)
        return resp

    def changePosition(self, thing, position):
        """ Change the position of a thing by name """
        for t in self._things :
            if 'NAME' in t:
                if t['NAME'] == thing and 'thingUri' in t:
                    thingUri = t['thingUri']
                    break
                else:
                    raise NameError(f'No thing with the name { thing } present.')
            else:
                raise NameError('No things available.')
        data = {
            "data": {
                "requestPosition": str(position)
            },
            "path": "/thing" + thingUri,
            "host": "https://thing.brunt.co:8080",
            "sessionId": self._sessionid
        }
        resp = self._http.request(self._s, data, RequestTypes.PUT)
        return resp

