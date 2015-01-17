from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    cmd = ".raw "

    def __init__(self, msg, share):
        super(Module, self).__init__(msg, share)

    def main(self):
        parsedRaw = self.parse(self.msg.MSG)
        if self.msg.FROM[3] == "Xyresic.SeniorModerator.AnimeBytes":
            self.sendcmd(parsedRaw[0], parsedRaw[1])
        return

    # Modified version of parse from irc.py (no need to parse prefix)
    def parse(self, line):
        cmdparam = []
        trailing = ""
        trailingStart = len(line)
        if " :" in line:
            trailingStart = line.find(" :")
            trailing = line[trailingStart + 2 : ]
        cmdparam = line[ : trailingStart].strip().split(" ")
        return (cmdparam, trailing)
