import re
import json
import http
import math
import urllib
import threading
import html.parser

from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    cmd = ".poll"

    def __init__(self, msg, queue):
        super(Module, self).__init__(msg, queue)
        self.data = json.load(open("modules/data/AB-polls", "r"))

    def run(self):

        # Set some variables from loaded json file and message
        site = self.data["site"]
        AB = http.client.HTTPSConnection(site)
        webheader = self.data["webheader"]
        logininfo = urllib.parse.urlencode(self.data["logininfo"])
        args = [x for x in self.msg["MSG"].split(' ') if x]

        # Login to AB and set cookie in webheader
        resp = self.reqPage(AB, "POST", "/login.php", logininfo, webheader)
        if resp != None:
            cookie = resp.getheader("Set-Cookie").split(", ")
            if [x for x in cookie if "session=" in x]:
                cookie = [x for x in cookie if "session=" in x][0].split(";")[0]
                webheader.update({"Cookie" : cookie})
                json.dump(self.data, 
                          open("modules/data/AB-polls", "w"), indent=4)
        else:
            self.sendmsg("Login Failed")

        # Try to search for a expanded version of args[0]
        try:
            temp_url = self.data[args[0]]
        except:
            temp_url = args[0]

        pollurl = urllib.parse.urlparse(temp_url)
        
        # If the URL is from AB, proceed
        if site == pollurl.netloc:
            
            # If it's 3 arguments, add to dictionary, ignore extra args
            if len(args) >= 2:
                self.data[args[1]] = args[0]
                json.dump(self.data, 
                           open("modules/data/AB-polls", "w"), indent=4)

            # Run the poll command
            self.pollvotes(AB, webheader, pollurl)

        # Otherwise deny the request or we will end up sending the session
        # cookie to a potentially malicious server
        else:
            self.sendmsg("Check URL")

        return

    def pollvotes(self, AB, webheader, pollurl):
        
        page = self.reqHTML(AB, "GET", pollurl.path + '?' + pollurl.query,
                                None, webheader)

        question = re.search("(?<=id=\"threadpoll\").*?<strong>.*?<[/]strong>", page, re.DOTALL).group(0)
        question = re.search("(?<=<strong>).*(?=<[/]strong>)", question).group(0)
        series = re.findall("(?<=<li class=\"tleft\">).*(?=</li>)", page)
        percent = re.compile("(?<=\()\d{0,3}\.?\d{2}(?=\%\))")
        
        # At the end it looks like ['title', 'votes', '|*votes']
        votes = [[re.sub(percent, '', s)[:-3], percent.search(s).group(0)]
                 for s in series]
        votes = [[re.sub('\t', '', v[0]).strip(), v[1]] for v in votes]
        votes = [[html.parser.HTMLParser().unescape(v[0]), v[1],
                  '|' * int(math.ceil(float(v[1])))]
                 for v in votes]

        maxlen_title = max([len(t[0]) for t in votes])
        maxlen_total = max([len(t[0]) + len(t[2]) for t in votes])
        
        self.sendmsg(question)
        self.sendmsg("==== ==== ==== ====")

        for vote in votes:
            if maxlen_total <= 55:
                pad = ' ' * (maxlen_title - len(vote[0]))
                self.sendmsg("{}{} {}".format(pad, vote[0], vote[2]))
            else:
                self.sendmsg(vote[0])
                self.sendmsg(vote[2])
