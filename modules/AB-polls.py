import re
import json
import http
import urllib
import threading

from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    cmd = ".poll"

    def __init__(self, msg, queue):
        super(Module, self).__init__(msg, queue)
        self.data = json.load(open("modules/data/AB-polls", "r"))

    def run(self):

        # Set some variables from loaded json file and message
        site = self.data["site"]
        webheader = self.data["webheader"]
        logininfo = self.data["logininfo"]
        pollurl = urllib.parse.urlparse(self.msg["MSG"])

        self.sendmsg(pollurl)
        
        # Login to AB and set cookie in webheader
        AB = http.client.HTTPSConnection(site)
        resp = self.reqPage(AB, "POST", "/login.php", webheader, logininfo)
        if resp != None:
            cookie = resp.getheader("Set-Cookie").split(", ")
            cookie = [x for x in cookie if "session=" in x][0].split(";")[0]
            webheader.update({"Cookie" : cookie})
        else:
            self.sendmsg("Login Failed")
        
        return
