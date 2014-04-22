import re

from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    regex = "(.*\))( used the blacklisted IP )(.*)( and.*DNSBL)"

    def __init__(self, msg, share):
        super(Module, self).__init__(msg, share)

    def main(self):
        m = re.search(Module.regex, self.msg["MSG"])
        self.sendmsg(m.groups())
        return
