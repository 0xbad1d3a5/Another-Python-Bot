from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    # Defines the command that triggers the module
    cmd = ".example_command"

    def __init__(self, msg, queue):
        super(Module, self).__init__(msg, queue)

    def main(self):
        
        # Send "Hello World!" to the user/channel that triggered the command
        self.sendmsg("Hello World!")
        return
