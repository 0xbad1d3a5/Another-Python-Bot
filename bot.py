#!/usr/bin/python3
import sys
import os
import re
import socket
import http.client
import importlib
import queue
import traceback

import sqlite3

import modules

## This is the class that will communicate with the IRC server ##
#################################################################
class irc:
    
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

    def connect(self, info):
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.HOST, self.PORT))
        self.s.send("NICK {}\r\n".format(self.NICK).encode("utf-8"))
        self.s.send("USER {} 0 * :{}\r\n"
                    .format(self.IDENT, self.REALNAME).encode("utf-8"))
        self.run()

    # Send a command to IRC
    def sendcmd(self, cmd, msg):
        self.s.send("{} :{}\r\n".format(cmd, msg)
                    .encode("utf-8", errors="ignore"))

    def run(self):

        self.buffer = self.buffer + self.s.recv(512).decode("utf-8")
        temp = self.buffer.split("\n")
        self.buffer = temp.pop()
        
        for l in temp:

            m = self.parse(l)
 
            # PING - play PING PONG with the server
            if m[1] == "PING":
                self.sendcmd("PONG", m[3])

            # PRIVMSG - any sort of message
            elif m[1] == "PRIVMSG":
                print("{}\n{} from {} - {}".format(m[0], m[1], m[2], m[3]))

            # RPL_LUSERME - good place to join channels
            elif m[1] == "255":
                channels = self.CHANNELS.split(",")
                for c in channels:
                    self.sendcmd("JOIN", c)
                    
            # UNIMPLEMENTED - do nothing for the rest of the commands
            else:
                print("{} - NEEDS HANDLING\nparams: {}\ntrailing: {}\n"
                      .format(m[1], m[2], m[3]))

## MAIN PROGRAM ##
##################

# Import the modules from the modules directory
modules = [importlib.import_module("." + x, package="modules")
           for x in modules.__all__]

q = queue.Queue()

for m in modules:
    mclass = getattr(m, "module")
    thread = mclass("Hello World!", q)
    thread.start()

while not q.empty():
    print(q.get())

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

# Create a new irc object
try:
    IRC = irc(info)
except KeyError:
    print("Error in info file")
    sys.exit(1)

IRC.connect(info)

while 1:
    IRC.run()
