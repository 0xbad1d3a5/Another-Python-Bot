import re
import json
import threading

from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    cmd = ".poll"

    def __init__(self, msg, queue):
        super(Module, self).__init__(msg, queue)
        self.data = json.load(open("modules/data/AB-polls", "r"))

    def run(self):
        
        return
