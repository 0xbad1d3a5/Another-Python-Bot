from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    cmd = ".help"

    def __init__(self, msg, share):
        super(Module, self).__init__(msg, share)

    def main(self):
        self.sendpm(".mei [url] - upload a image to AB")
        self.sendpm(".8ball [question]")
        self.sendpm(".poll <url/opt> <opt> - display poll results on AB")
        return
