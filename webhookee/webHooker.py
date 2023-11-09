import falcon
import base64
import json
import os

user_accounts = { "user1": "mypass1", "admin": "P@ssw0rd" }

api_keys = [ "upupdowndonleftrightleftrightBA","01234567890abcdef" ]

class Authorize(object):
    def __init__ (self) :
        from mylogger import set_up_logging
        self.logger = set_up_logging("wbh-")

    def __auth_basic(self, username, password) :
        self.logger.info(f"{username} {password} in {user_accounts}")
        if username in user_accounts and user_accounts [username] == password:
            self.logger.info('your have access - welcom')
        else:
            self.logger.warn(f"Unauthorized, Your access is not allowed")
            raise falcon.HTTPUnauthorized( 'Unauthorized', 'Your access is not allowed')

    def __auth_apikey(self,apiKeyVal):
        self.logger.info(f"GOT apiKeyVal = {apiKeyVal}")
        if apiKeyVal in api_keys:
            self.logger.info('your have access - welcom')
        else:
            self.logger.warn(f"Unauthorized, Your access is not allowed")
            raise falcon.HTTPUnauthorized( 'Unauthorized', 'Your access is not allowed')


    def __call__(self, req, resp,resource, params):
        self.logger.info(f'before trigger - class: Authorize {req.auth}')
        self.logger.info(f"{req.headers}")
        auth_exp = req.auth.split(' ') if req.auth is not None else (None, None, )

        if auth_exp[0] is not None and auth_exp[0].lower() == "basic":
            auth = base64.b64decode(auth_exp[1]).decode('utf-8').split(":")
            username = auth[0]
            password = auth[1]
            self.logger.info(f"{auth}")
            self.__auth_basic(username, password)
        elif "APIKEY" in req.headers.keys():
            apiKeyVal =req.headers.get("APIKEY")
            self.__auth_apikey(apiKeyVal)
        else:
            raise falcon.HTTPNotImplemented ( 'Not Implement', "You don't use the right auth method")

class WhSessionInfo:

    def __init__(self):
        from mylogger import set_up_logging
        self.logger = set_up_logging("wbh-")

    def on_get(self, req, resp):
        dicRes = {}
        if os.path.exists("/tmp/lastSessionInfo"):
            with open("/tmp/lastSessionInfo","r") as fi:
               dicRes = json.load(fi)
            os.remove("/tmp/lastSessionInfo")

        resp.status = falcon.HTTP_200
        resp.content_type = 'application/json'
        resp.context['result'] = dicRes

    @falcon.before(Authorize())
    def on_post(self, req, resp):
        evtData = req.context['doc']
        print(f"{json.dumps(evtData,indent=2)}")
        self.logger.info(f"{evtData}")
        resp.content_type = 'application/json'
        with open("/tmp/lastSessionInfo","w") as fo:
            json.dump(evtData,fo)
        resp.status = falcon.HTTP_200
        resp.context['result'] = {"status":"ok"}

"""
app = falcon.App()
"""
from falcon_util import RequireJSON, JSONTranslator
app = falcon.App(middleware=[
        RequireJSON(),
        JSONTranslator()
])
app.add_route('/callback/sessionInfo', WhSessionInfo())

