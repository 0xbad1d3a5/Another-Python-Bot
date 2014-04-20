from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    cmd = ".help"

    def __init__(self, msg, comm):
        super(Module, self).__init__(msg, comm)

    def main(self):
        self.sendpm(".mei [url] - upload a image to AB")
        self.sendpm(".poll <url/opt> <opt> - display poll results on AB")
        return
