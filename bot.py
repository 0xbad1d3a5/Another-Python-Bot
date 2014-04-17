#!/usr/bin/python3
import os
import re
import sys
import imp
import queue
import socket
import select
import importlib
import traceback
import http.client

import modules

## This is the class that will communicate with the IRC server ##
#################################################################
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
        self.EXTRA = info["EXTRA"]

        # Buffer for buffering messages from socket
        self.buffer = ""

    # Returns a list containing a parsed IRC message
    # :<prefix> <command> <params> :<trailing>
    # ['prefix', 'command' '['param1', 'param2', '...']', 'trailing']
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

    def readSocket(self):
        (read, write, excep) = select.select([self.s], [], [], 0)
        if read:
            return read[0].recv(512).decode("utf-8")
        else:
            return ""

    def writeSocket(self, string):
        (read, write, excep) = select.select([], [self.s], [], 5)
        try:
            write[0].sendall("{}\r\n".format(string)
                             .encode("utf-8", errors="ignore"))
        except:
            print("Socket write error: blocked for more than 5s")
            sys.exit(1)

    # Connect to the server using the information given
    def connect(self, info):
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.HOST, self.PORT))
        self.s.setblocking(0)
        
        self.writeSocket("NICK {}".format(self.NICK))
        self.writeSocket("USER {} 0 * :{}"
                         .format(self.IDENT, self.REALNAME))

    # Send a command to IRC
    def sendcmd(self, cmd, params, msg):
        if params:
            params = " ".join(params)
            self.writeSocket("{} {} :{}".format(cmd, params, msg))
        else:
            self.writeSocket("{} :{}".format(cmd, msg))

    # Return one parsed line from the socket (only returns on PRIVMSG)
    def getmsg(self):
        
        # Append buffer with new incoming text
        self.buffer = self.buffer + self.readSocket()
        
        # Get a line and remove from buffer
        lineEnd = self.buffer.find("\n") + 1
        line = self.buffer[ : lineEnd]
        self.buffer = self.buffer[lineEnd : ]

        # If line is not empty, process it
        if line:
            
            msg = self.parse(line)
        
            # PING - play PING PONG with the server
            if msg["CMD"] == "PING":
                self.sendcmd("PONG", None, msg["MSG"])
        
            # RPL_ENDOFMOTD - Use this message to JOIN channels at start
            elif msg["CMD"] == "376":
                channels = self.CHANNELS.split(",")
                for c in channels:
                    self.sendcmd("JOIN", None, c)
    
            # INVITE - accept all channel invites automatically
            elif msg["CMD"] == "INVITE":
                self.sendcmd("JOIN", None, msg["MSG"])

            # PRIVMSG - any sort of message
            elif msg["CMD"] == "PRIVMSG":
                # If it's a PM, then replace <params> with sender
                # This is so we don't try to send messages to ourself
                if msg["PARAMS"][0][:1] not in ['#', '$']:
                    msg["PARAMS"][0] = msg["PRE"][1:msg["PRE"].find("!")]
                
            # UNIMPLEMENTED - do nothing for the rest of the commands
            else:
                print("COMMAND {} - NEEDS HANDLING".format(msg["CMD"]))
                print("prefix: {}\nparams: {}\ntrailing: {}"
                      .format(msg["PRE"], msg["PARAMS"], msg["MSG"]))
            
            return msg

## MAIN PROGRAM ##
##################

# Get settings from info file
try:
    info = {}
    file_info = open("info", "r")
    for line in file_info:
        (key, val) = line.strip("\n").split("=")
        info[key.upper()] = val
except IOError:
    print("File Not Found: \"info\"")
    sys.exit(1)

# Create a new IRC instance and connect
try:
    irc = IRC(info)
    irc.connect(info)
except KeyError:
    print("Error in info file")
    sys.exit(1)

# Import the modules from the modules directory
moduleList = [importlib.import_module("." + mod, package="modules")
           for mod in modules.__all__]
queue = queue.Queue()

while True:

    msg = irc.getmsg()
    
    if msg:
        
        if msg["MSG"] == ".reload":
            for mod in moduleList:
                try:
                    mod = imp.reload(mod)
                except:
                    irc.sendcmd(msg["CMD"], msg["PARAMS"], 
                                "RELOAD {} FAILED".format(moduleClass))
            irc.sendcmd(msg["CMD"], msg["PARAMS"], "Reloaded Modules")
            
        for mod in moduleList:
            moduleClass = getattr(mod, "module")
            if moduleClass.cmd == msg["MSG"][:len(moduleClass.cmd)]:
                try:
                    thread = moduleClass(msg, queue)
                    thread.start()
                except:
                    irc.sendcmd(msg["CMD"], msg["PARAMS"], 
                                "MODULE {} FAILED".format(moduleClass))
    
    while not queue.empty():
        reply = queue.get()
        irc.sendcmd(reply["CMD"], reply["PARAMS"], reply["MSG"])
