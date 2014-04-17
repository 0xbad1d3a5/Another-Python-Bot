import re
import json
import threading

class Module(threading.Thread):

    # Defines the command that triggers the module
    cmd = ".poll"

    def __init__(self, msg, queue):
        super(Module, self).__init__()
        self.msg = msg
        self.queue = queue
        self.data = json.load(open("modules/data/AB-polls", "r"))

    def run(self):
        
        return
