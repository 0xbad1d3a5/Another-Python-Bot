import re
import json
import http
import math
import urllib
import html.parser

from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    cmd = ".poll"

    def __init__(self, msg, queue):
        super(Module, self).__init__(msg, queue)
        self.data = json.load(open("data/AB-polls", "r"))

    def main(self):

        # Set some variables from loaded json file and message
        site = self.data["site"]
        AB = http.client.HTTPSConnection(site)
        webheader = self.data["webheader"]
        polldict = self.data["polldict"]
        logininfo = urllib.parse.urlencode(self.data["logininfo"])
        args = [x for x in self.msg["MSG"].split(' ') if x]

        # Login to AB and set cookie in webheader
        resp = self.reqPage(AB, "POST", "/login.php", logininfo, webheader)
        if resp != None:
            cookie = resp.getheader("Set-Cookie").split(", ")
            if [x for x in cookie if "session=" in x]:
                cookie = [x for x in cookie if "session=" in x][0].split(";")[0]
                webheader.update({"Cookie" : cookie})
        else:
            self.sendmsg("Login Failed")

        # Try to search for a expanded version of args[0]
        try:
            temp_url = polldict[args[0]]
        except:
            temp_url = args[0]

        pollurl = urllib.parse.urlparse(temp_url)
        
        # If the URL is from AB, proceed
        if site == pollurl.netloc:
            page = self.reqHTML(AB, "GET", pollurl.path + '?' 
                                + pollurl.query, None, webheader)
            check = self.checkpoll(page)
            if check == 2:
                page = self.voteblank(AB, pollurl, webheader)
            if check == 1 or check == 2:
                # If it's 3 arguments, add to dictionary, ignore extra args
                if len(args) >= 2:
                    polldict[args[1]] = args[0]
                    del webheader["Cookie"]
                    json.dump(self.data, 
                              open("modules/data/AB-polls", "w"), indent=4)
                # Run the poll command
                self.pollvotes(page)

        # Otherwise deny the request or we will end up sending the session
        # cookie to a potentially malicious server
        else:
            self.sendmsg("Check URL")

        return

    # Checks whether the thread has a poll or not
    # Returns 1 if there's a poll, 0 if no poll, 2 if not voted
    def checkpoll(self, page):
        haspoll = re.search("id=\"threadpoll\"", page)
        if haspoll:
            not_voted = re.search("id=\"answer_0\"", page)
            if not_voted:
                return 2
            return 1
        else:
            return 0

    # Sends a POST request and votes blank, returns new page
    def voteblank(self, AB, pollurl, webheader):
        threadid = re.search("threadid=[0-9]*", pollurl.query).group(0)
        reqbody = "action=poll&large=1&" + threadid + "&vote=0"
        self.reqPage(AB, "POST", "/index.php", reqbody, webheader)
        return self.reqHTML(AB, "GET", pollurl.path + '?'
                            + pollurl.query, None, webheader)

    # Parse the HTML, format and send the poll for IRC
    def pollvotes(self, page):
        question = re.search("(?<=id=\"threadpoll\").*?<strong>.*?<[/]strong>", page, re.DOTALL).group(0)
        question = re.search("(?<=<strong>).*(?=<[/]strong>)", question).group(0)
        question = html.parser.HTMLParser().unescape(question)
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
