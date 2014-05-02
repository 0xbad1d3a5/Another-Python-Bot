import re
import json
import http
import urllib
import random
import html.parser

from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    # Defines the command that triggers the module
    cmd = ".random "

    def __init__(self, msg, share):
        super(Module, self).__init__(msg, share)

    def main(self):
        
        data = json.load(open("data/AB-random", "r"))
        AB = http.client.HTTPSConnection(data["site"])
        webheader = data["webheader"]
        logininfo = urllib.parse.urlencode(data["logininfo"])
        seriesurl = data["seriesurl"]
        silentchannels = data["silentchannels"]

        # Login to AB
        resp = self.reqPage(AB, "POST", "/login.php", logininfo, webheader)
        if resp != None:
            cookie = resp.getheader("Set-Cookie").split(", ")
            if [x for x in cookie if "session=" in x]:
                cookie = [x for x in cookie if "session=" in x][0].split(";")[0]
                webheader.update({"Cookie" : cookie})
        else:
            self.sendmsg("Login Failed")

        # Get serieslist.php
        series_list = ["anime", "manga", "visual_novels"]
        search_type = None
        try: search_type = self.args[0] if self.args[0] in series_list else "anime"
        except: pass

        series_page = self.reqHTML(AB, "GET", "/serieslist.php" + "?type=" + search_type, None, webheader)
        page_nums = re.findall("(?<=page=)\d*", series_page)
        page_max = max([int(x) for x in page_nums])
        rand_page = str(random.randint(1, page_max))

        # Get the random page from serieslist.php
        series_page = self.reqHTML(AB, "GET", "/serieslist.php" + "?type=" + search_type + "&page=" + rand_page, None, webheader)
        list_series = re.findall("(?<=series.php\?id=)\d*", series_page)
        rand_series = random.choice(list_series)

        print(self.msg.TO)
        if self.msg.TO[1].lower() in silentchannels:
            self.sendcmd(("NOTICE", self.msg.FROM[1]), seriesurl + "?id=" + rand_series)
        else:
            self.sendmsg(seriesurl + "?id=" + rand_series)

        return
