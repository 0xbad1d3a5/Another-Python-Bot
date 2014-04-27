import sys
import socket
import select
import traceback

#### IRC COMMUNICATION CLASS ####
#################################
# This class communicates with the IRC server
class IRC:
    
    def __init__(self, HOST, PORT):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((HOST, int(PORT)))
        self.s.setblocking(0)
        self.buffer = ""

    def read(self):
        (read, write, excep) = select.select([self.s], [], [], 0)
        if read: return read[0].recv(512).decode("utf-8", errors="ignore")
        else: return ""

    def write(self, string):
        (read, write, excep) = select.select([], [self.s], [], 10)
        try:
            write[0].sendall(string.encode("utf-8", errors="ignore"))
        except: 
            print("Socket write error") 
            sys.exit(1)

    """
    Parses a IRC message into its components
    IRC MESSAGE FORMAT = ":<prefix> <command> <params> :<trailing>\r\n"
    Returns a tuple in the format (pre, cmd, args, msg)
    """
    def parse(self, line):
        
        # Helper function that finds the nth position of a substring
        def findn(string, sub, n):
            start = string.find(sub)
            while start >= 0 and n > 1:
                start = string.find(sub, start+len(sub))
                n -= 1
            if start < 0:
                raise Exception("IRC.parse: parse error")
            return start

        prefix = ""
        cmdparam = []
        trailing = ""
        prefixEnd = 0
        trailingStart = len(line)

        # Message has a prefix
        if line[:1] == ":":
            prefixEnd = findn(line, " ", 1)
            prefix = line[ : prefixEnd]

        # Message has trailing arguments
        if " :" in line:
            trailingStart = findn(line, " :", 1)
            trailing = line[trailingStart + 2 : ].strip()

        cmdparam = line[prefixEnd : trailingStart].strip().split(" ")

        return (prefix, cmdparam[0], cmdparam[1:], trailing)

    # Returns one server_msg from the buffer, or None
    def getmsg(self):
        
        # Append buffer with new incoming text
        self.buffer = self.buffer + self.read()
        
        # Get a line and remove from buffer
        lineEnd = self.buffer.find("\n") + 1
        line = self.buffer[ : lineEnd]
        self.buffer = self.buffer[lineEnd : ]

        # If line is not empty, handle it
        if line:
            return self.parse(line)
        else:
            return None
