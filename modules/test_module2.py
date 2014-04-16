import threading

from datetime import datetime

class module(threading.Thread):

    cmd = ".world"

    def __init__(self, m, q):
        super(module, self).__init__()
        self.m = m
        self.q = q
        print("Thread .hello created on {}\n".format(datetime.now()))

    def run(self):
        self.q.put(self.m)
        return
