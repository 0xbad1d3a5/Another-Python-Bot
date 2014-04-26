import http
import inspect
import threading
import traceback

class BaseModule(threading.Thread):

    def __init__(self, msg, share):
        super(BaseModule, self).__init__()
        self.msg = msg
        self.args = [arg for arg in msg.MSG.split(' ') if arg]
        self.share = share
        
    # Main entrypoint for thread, override this
    def main(self):
        raise NotImplementedError

    # Do not override! Allows bot to inform sender a module has crashed
    def run(self):
        try:
            self.main()
        except:
            mem = inspect.getmembers(self)
            name = [n[1] for n in mem if n[0] == "__class__"][0]
            self.sendmsg("THREAD {} HAS CRASHED".format(name))
            print(traceback.print_exc())

    # Send a command
    def sendcmd(self, cmd, text=None):
        self.share.put_queue((cmd, text))

    # Send a message to where the message came from
    def sendmsg(self, string):
        if self.share.NICK == self.msg.TO[1]: self.msg.TO[1] = self.msg.FROM[1]
        self.sendcmd(("PRIVMSG", self.msg.TO[1]), string)

    # Send a PM to the user who triggered the command
    def sendpm(self, string):
        self.sendcmd(("PRIVMSG", self.msg.FROM[1]), string)

    # Send a message to the specified target
    def sendto(self, target, string):
        self.sendcmd(("PRIVMSG", target), string)

    # Request a page and return either RESPONSE or actual HTML
    def _requestPage(self, conn, method, url, body, header, resptype):
        try:
            conn.request(method, url, body, header)
            resp = conn.getresponse()
            conn.close()
            if resptype == 0: return resp
            elif resptype == 1: return resp.read().decode("utf-8")
        except:
            return None

    # Request a HTML page from the connection and return the RESPONSE
    def reqPage(self, conn, method, url, body, header):
        return self._requestPage(conn, method, url, body, header, 0)
    
    # Request a HTML page from the connection and return the HTML
    def reqHTML(self, conn, method, url, body, header):
        return self._requestPage(conn, method, url, body, header, 1)        
