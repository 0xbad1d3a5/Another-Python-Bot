import threading

class module(threading.Thread):

    cmd = ".hello"

    def __init__(self, msg, q):
        super(module, self).__init__()
        self.msg = msg
        self.q = q

    def run(self):
        self.q.put(self.msg)
        return
