import socket
import select

## IRC COMMUNICATION CLASS ##
#############################
# This class communicates with the IRC server
class IRC:
    
    # Initialize the variables for IRC stuff
    # info is a dictionary containing connection information
    def __init__(self, info):
        
        self.HOST = info["HOST"]
        self.PORT = int(info["PORT"])
        self.CHANNELS = info["CHANNELS"]
        self.NICK = info["NICK"]
        self.IDENT = info["IDENT"]
        self.REALNAME = info["REALNAME"]
        self.EXTRAS = info["EXTRAS"]

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.buffer = ""

    def read(self):
        (read, write, excep) = select.select([self.s], [], [], 0)
        if read:
            return read[0].recv(512).decode("utf-8", errors="ignore")
        else:
            return ""

    def write(self, cmd, text=None):
        temp = ' '.join(cmd)
        if text:
            temp = "{} :{}".format(temp, text)[:510]
        temp = temp + "\r\n"
        
        (read, write, excep) = select.select([], [self.s], [], 10)
        try:
            write[0].sendall(temp.encode("utf-8", errors="ignore"))
        except:
            print("Socket write error")
            sys.exit(1)

    # Send a raw command to IRC
    def write_raw(self, string):
        (read, write, excep) = select.select([], [self.s], [], 10)
        try:
            write[0].sendall("{}\r\n".format(string)
                             .encode("utf-8", errors="ignore"))
        except:
            print("Socket write error")
            sys.exit(1)

    # Connect to the server using the information given
    def connect(self):        
        self.s.connect((self.HOST, self.PORT))
        self.s.setblocking(0)        
        self.write(("NICK", self.NICK))
        self.write(("USER", self.IDENT, "0", "*"), self.REALNAME)

    # Parses a IRC message into its components
    # IRC MESSAGE FORMAT = ":<prefix> <command> <params> :<trailing>\r\n"
    # Returns a server_msg dict - FORMAT:
    # ['PRE':<prefix>, 'CMD':<cmd>, 'PARAMS':[<p1>, ...], 'MSG':<trailing>]
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
        return {"PRE":prefix, "CMD":cmdparam[0],
                "PARAMS":cmdparam[1:], "MSG":trailing}

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
