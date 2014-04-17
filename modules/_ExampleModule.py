import threading

from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    # Defines the command that triggers the module
    cmd = ".example_command"

    def __init__(self, msg, queue):
        super(Module, self).__init__(msg, queue)

    def run(self):
        
        self.sendmsg("Hello World!")
        return
