#!/usr/bin/python3
import os
import re
import imp
import sys
import time
import json
import queue
import socket
import select
import importlib
import http.client

import modules

# Import the modules from the modules directory
moduleList = [importlib.import_module("." + mod, package="modules")
           for mod in modules.__all__]
# Queue that modules write to to communicate in IRC
queue = queue.Queue()

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

    def readSocket(self):
        (read, write, excep) = select.select([self.s], [], [], 0)
        if read:
            return read[0].recv(512).decode("utf-8")
        else:
            return ""

    def writeSocket(self, string):
        (read, write, excep) = select.select([], [self.s], [], 10)
        try:
            write[0].sendall("{}\r\n".format(string)
                             .encode("utf-8", errors="ignore"))
        except:
            print("Socket write error")
            sys.exit(1)

    # Connect to the server using the information given
    def connect(self, info):        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.HOST, self.PORT))
        self.s.setblocking(0)        
        self.writeSocket("NICK {}".format(self.NICK))
        self.writeSocket("USER {} 0 * :{}".format(self.IDENT, self.REALNAME))

    # Send a command to IRC
    def sendcmd(self, cmd, params, msg):
        if params:
            params = " ".join(params)
            self.writeSocket("{} {} :{}".format(cmd, params, msg))
        else:
            self.writeSocket("{} :{}".format(cmd, msg))

    # Send a message to message origin on IRC
    def sendmsg(self, msg, string):
        # If it's a PM, then replace TO with sender
        # This is so we don't try to send messages to ourself
        if msg["TO"][:1] not in ['#', '$']:
            msg["TO"] = msg["FROM"][1:msg["FROM"].find("!")]
        self.sendcmd("PRIVMSG", [msg["TO"]], string)

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

    # Processes IRC messages
    # Returns a msg dict on PRIVMSG - FORMAT:
    # ['FROM':<sender>, 'TO':<channel/user>, 'MSG':<message>]
    # Returns None if server_msg is not a PRIVMSG
    def getmsg(self):
        
        # Append buffer with new incoming text
        self.buffer = self.buffer + self.readSocket()
        
        # Get a line and remove from buffer
        lineEnd = self.buffer.find("\n") + 1
        line = self.buffer[ : lineEnd]
        self.buffer = self.buffer[lineEnd : ]

        # If line is not empty, process it
        if line:
            
            server_msg = self.parse(line)
        
            # PING - play PING PONG with the server
            if server_msg["CMD"] == "PING":
                self.sendcmd("PONG", None, server_msg["MSG"])
        
            # RPL_ENDOFMOTD / ERR_NOMOTD - join channels here
            elif server_msg["CMD"] in ["376", "422"]:
                channels = self.CHANNELS.split(",")
                for c in channels:
                    self.sendcmd("JOIN", None, c)
    
            # INVITE - accept all channel invites automatically
            elif server_msg["CMD"] == "INVITE":
                self.sendcmd("JOIN", None, server_msg["MSG"])

            # PRIVMSG - any sort of message
            elif server_msg["CMD"] == "PRIVMSG":
                return {"FROM" : server_msg["PRE"],
                        "TO" : server_msg["PARAMS"][0],
                        "MSG" : server_msg["MSG"]}
                
            # UNIMPLEMENTED - do nothing for the rest of the commands
            else:
                print("COMMAND {} - NEEDS HANDLING".format(server_msg["CMD"]))
                print("prefix: {}\nparams: {}\ntrailing: {}".format(server_msg["PRE"], server_msg["PARAMS"], server_msg["MSG"]))

## MAIN PROGRAM ##
##################

# Get settings from info file
try:
    file_info = open("info", "r")
    info = json.load(file_info)
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

while True:

    time.sleep(0.05)
    msg = irc.getmsg()
    
    if msg:
        
        if msg["MSG"] == ".reload":
            for mod in moduleList:
                try:
                    mod = imp.reload(mod)
                except:
                    irc.sendmsg(msg, "RELOAD {} FAILED".format(moduleClass))
            irc.sendmsg(msg, "Reloaded Modules")
            
        for mod in moduleList:
            moduleClass = getattr(mod, "Module")
            if moduleClass.cmd == msg["MSG"][:len(moduleClass.cmd)]:
                try:
                    msg["MSG"] = msg["MSG"][len(moduleClass.cmd):].strip()
                    thread = moduleClass(msg, queue)
                    thread.start()
                except:
                    irc.sendmsg(msg, "MODULE {} FAILED".format(moduleClass))
    
    while not queue.empty():
        reply = queue.get()
        irc.sendmsg(reply, reply["MSG"])
