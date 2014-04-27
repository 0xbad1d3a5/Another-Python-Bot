import random

from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    cmd = ".8ball "

    def __init__(self, msg, share):
        super(Module, self).__init__(msg, share)

    def main(self):
        num = random.randint(1, 20)
        if num == 1:
            self.sendmsg("It is certain")
        elif num == 2:
            self.sendmsg("It is decidedly so")
        elif num == 3:
            self.sendmsg("Without a doubt")
        elif num == 4:
            self.sendmsg("Yes definitely")
        elif num == 5:
            self.sendmsg("You may rely on it")
        elif num == 6:
            self.sendmsg("As I see it, yes")
        elif num == 7:
            self.sendmsg("Most likely")
        elif num == 8:
            self.sendmsg("Outlook good")
        elif num == 9:
            self.sendmsg("Yes")
        elif num == 10:
            self.sendmsg("Signs point to yes")
        elif num == 11:
            self.sendmsg("Reply hazy try again")
        elif num == 12:
            self.sendmsg("Ask again later")
        elif num == 13:
            self.sendmsg("Better not tell you now")
        elif num == 14:
            self.sendmsg("Cannot predict now")
        elif num == 15:
            self.sendmsg("Concentrate and ask again")
        elif num == 16:
            self.sendmsg("Don't count on it")
        elif num == 17:
            self.sendmsg("My reply is no")
        elif num == 18:
            self.sendmsg("My sources say no")
        elif num == 19:
            self.sendmsg("Outlook not so good")
        elif num == 20:
            self.sendmsg("Very doubtful")
        return
