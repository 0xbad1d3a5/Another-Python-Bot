from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    regex = "\001VERSION\001"

    def __init__(self, msg, share):
        super(Module, self).__init__(msg, share)

    def main(self):
        self.sendcmd(("NOTICE", self.msg.FROM[1]), "\001VERSION Another Python Bot v0.1\001")
        return
