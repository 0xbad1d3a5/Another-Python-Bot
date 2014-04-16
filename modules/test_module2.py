import threading

class module(threading.Thread):

    cmd = ".world"

    def __init__(self, m, q):
        super(module, self).__init__()
        self.m = m
        self.q = q

    def run(self):
        self.q.put(self.m)
        return
