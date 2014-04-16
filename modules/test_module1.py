import threading

class module(threading.Thread):

    cmd = ".hello"

    def __init__(self, m, q):
        super(module, self).__init__()
        self.m = m
        self.q = q
        print("Thread .hello created!")

    def run(self):
        self.q.put(self.m)
