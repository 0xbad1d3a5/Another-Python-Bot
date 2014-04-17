import threading

from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    # Defines the command that triggers the module
    cmd = ".help"

    def __init__(self, msg, queue):
        super(Module, self).__init__(msg, queue)

    def run(self):

        self.sendpm(".mei [url] - upload a image to AB")
        self.sendpm(".poll <optional> [url] - display poll results on AB")
        return
