import threading

class BaseModule(threading.Thread):

    def __init__(self, msg, queue):
        super(BaseModule, self).__init__()
        self.msg = msg
        self.queue = queue

    # Send a message to where the message came from (either user/channel)
    def sendmsg(self, string):
        self.queue.put({"TO":msg["TO"], "FROM":self.msg["FROM"],
                        "MSG":string})

    # Send a PM to the user who triggered the command
    def sendpm(self, string):
        self.queue.put({"TO":"", "FROM":self.msg["FROM"],
                        "MSG":string})
