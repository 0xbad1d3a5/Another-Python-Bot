import threading

class Module(threading.Thread):

    # Defines the command that triggers the module
    cmd = ".example_command"

    def __init__(self, msg, queue):
        super(Module, self).__init__()
        self.msg = msg
        self.queue = queue

    def run(self):
        
        # Sends the same message back to origin
        self.queue.put(self.msg)
        return
