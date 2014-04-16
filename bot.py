#!/usr/bin/python3
import sys
import os
import re
import socket
import http.client
import importlib
import queue
import traceback

import modules

## This is the class that will communicate with the IRC server ##
#################################################################
class irc:
    
    # Initialize the variables for irc stuff
    # info is a dictionary containing connection information
    def __init__(self, info):
        
        self.HOST = info["HOST"]
        self.PORT = int(info["PORT"])
        self.CHANNELS = info["CHANNELS"]
        self.NICK = info["NICK"]
        self.IDENT = info["IDENT"]
        self.REALNAME = info["REALNAME"]
        self.EXTRA = info["EXTRA"]

        self.buffer = ""

    # Returns a list containing a parsed IRC message
    # :<prefix> <command> <params> :<trailing>
    # ['prefix', 'command' '['param1', 'param2', '...']', 'trailing']
    def parse(self, msg):
        
        # Helper function that finds the nth position of a substring
        def findn(string, sub, n):
            start = string.find(sub)
            while start >= 0 and n > 1:
                start = string.find(sub, start+len(sub))
                n -= 1
            if start < 0:
                raise Exception("irc.parse: parse error")
            return start

        prefix = ""
        cmdparam = []
        trailing = ""
        prefixEnd = 0
        trailingStart = len(msg)

        # Message has a prefix
        if msg[:1] == ":":
            prefixEnd = findn(msg, " ", 1)
            prefix = msg[ : prefixEnd]

        # Message has trailing arguments
        if " :" in msg:
            trailingStart = findn(msg, " :", 1)
            trailing = msg[trailingStart + 2 : ].strip()

        cmdparam = msg[prefixEnd : trailingStart].strip().split(" ")       
        return [prefix, cmdparam[0], cmdparam[1:], trailing]

    # Connect to the server using the information given
    def connect(self, info):
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.HOST, self.PORT))
        self.s.send("NICK {}\r\n".format(self.NICK).encode("utf-8"))
        self.s.send("USER {} 0 * :{}\r\n"
                    .format(self.IDENT, self.REALNAME).encode("utf-8"))

    # Send a command to IRC
    def sendcmd(self, cmd, params, msg):
        if params:
            params = "".join(params)
            self.s.send("{} {} :{}\r\n".format(cmd, params, msg)
                        .encode("utf-8", errors="ignore"))
        else:
            self.s.send("{} :{}\r\n".format(cmd, msg)
                        .encode("utf-8", errors="ignore"))

    # Run the irc connection and return a list of parsed PRIVMSG
    def run(self):

        self.buffer = self.buffer + self.s.recv(512).decode("utf-8")
        temp = self.buffer.split("\n")
        self.buffer = temp.pop()

        marray = []

        for l in temp:

            m = self.parse(l)

            # PING - play PING PONG with the server
            if m[1] == "PING":
                self.sendcmd("PONG", None, m[3])

            # RPL_LUSERME - Use this message to JOIN channels at start
            elif m[1] == "255":
                channels = self.CHANNELS.split(",")
                for c in channels:
                    self.sendcmd("JOIN", None, c)

            # INVITE - accept all channel invites automatically
            elif m[1] == "INVITE":
                self.sendcmd("JOIN", None, m[3])

            # PRIVMSG - any sort of message
            elif m[1] == "PRIVMSG":
                marray.append(m)
                
            # UNIMPLEMENTED - do nothing for the rest of the commands
            else:
                print("COMMAND {} - NEEDS HANDLING".format(m[1]))
                
        return marray

## MAIN PROGRAM ##
##################

# Get settings from info file
try:
    info = {}
    f = open("info", "r")
    for l in f:
        (key, val) = l.strip("\n").split("=")
        info[key.upper()] = val
except IOError:
    print("File Not Found: \"info\"")
    sys.exit(1)

# Create a new irc instance and connect
try:
    IRC = irc(info)
    IRC.connect(info)
except KeyError:
    print("Error in info file")
    sys.exit(1)

# Import the modules from the modules directory
modules = [importlib.import_module("." + x, package="modules")
           for x in modules.__all__]
q = queue.Queue()

while 1:
    
    marray = IRC.run()

    for m in marray:
        for mod in modules:
            mclass = getattr(mod, "module")
            if mclass.cmd == m[3][:len(mclass.cmd)]:
                thread = mclass(m, q)
                thread.start()

    while not q.empty():
        m = q.get()
        print(m)
        IRC.sendcmd(m[1], m[2], m[3])
