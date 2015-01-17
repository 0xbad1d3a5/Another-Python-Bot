import os
import random

from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    # Defines the command that triggers the module
    cmd = ".pick "

    def __init__(self, msg, share):
        super(Module, self).__init__(msg, share)

    def main(self):
        random.seed(os.urandom(64))
        self.sendmsg(self.msg.FROM[1] + ": " + random.choice(self.args))

        return
