import random

from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    cmd = ".8ball "

    def __init__(self, msg, share):
        super(Module, self).__init__(msg, share)

    def main(self):
        num = random.randint(1, 20)
        msg = ""
        if num == 1:
            msg = "It is certain"
        elif num == 2:
            msg = "It is decidedly so"
        elif num == 3:
            msg = "Without a doubt"
        elif num == 4:
            msg = "Yes definitely"
        elif num == 5:
            msg = "You may rely on it"
        elif num == 6:
            msg = "As I see it, yes"
        elif num == 7:
            msg = "Most likely"
        elif num == 8:
            msg = "Outlook good"
        elif num == 9:
            msg = "Yes"
        elif num == 10:
            msg = "Signs point to yes"
        elif num == 11:
            msg = "Reply hazy try again"
        elif num == 12:
            msg = "Ask again later"
        elif num == 13:
            msg = "Better not tell you now"
        elif num == 14:
            msg = "Cannot predict now"
        elif num == 15:
            msg = "Concentrate and ask again"
        elif num == 16:
            msg = "Don't count on it"
        elif num == 17:
            msg = "My reply is no"
        elif num == 18:
            msg = "My sources say no"
        elif num == 19:
            msg = "Outlook not so good"
        elif num == 20:
            msg = "Very doubtful"
            
        self.sendmsg(self.msg.FROM[1] + ": " + msg)
        
        return
