#!/usr/bin/python3
import os
import re
import sys
import imp
import time
import json
import queue
import socket
import select
import inspect
import traceback
import importlib
import http.client

import modules

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

    # Send a raw command to IRC
    def sendraw(self, string):
        self.writeSocket(string)

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

    # Connect to the server using the information given
    def connect(self):        
        self.s.connect((self.HOST, self.PORT))
        self.s.setblocking(0)        
        self.writeSocket("NICK {}".format(self.NICK))
        self.writeSocket("USER {} 0 * :{}".format(self.IDENT, self.REALNAME))

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
        self.buffer = self.buffer + self.readSocket()
        
        # Get a line and remove from buffer
        lineEnd = self.buffer.find("\n") + 1
        line = self.buffer[ : lineEnd]
        self.buffer = self.buffer[lineEnd : ]

        # If line is not empty, handle it
        if line:
            return self.parse(line)
        else:
            return None

## IRC BOT CLASS ##
###################
# This class decides what to do with the messages from IRC
class Bot:
    
    def __init__(self, info_filename):

        self.moduleList = [importlib.import_module("." + mod, package="modules") for mod in modules.__all__]

        # Get settings from info file and connect the bot
        try:
            self.queue = queue.Queue()
            self.info = json.load(open(info_filename, "r"))
            self.irc = IRC(self.info)
            self.irc.connect()
        except:
            print("\"info\" file not found or syntax error")
            sys.exit(1)

    def run(self):

        while True:

            # Sleep so we don't eat the CPU alive
            time.sleep(0.05)
            
            # Handle IRC commands
            server_msg = self.irc.getmsg()
            if server_msg:
                self.handle(server_msg)

            # Process responses from modules
            while not self.queue.empty():
                response = self.queue.get()
                self.irc.sendmsg(response, response["MSG"])

    # Reloads all modules, loads any new modules as well
    # TODO: Should be importlib.reload(), but that's not implemented on 3.2
    # Fall back to imp instead until 3.2+ is considered stable enough
    def reloadmodules(self, msg):
        
        # Reload the modules folder, find any new modules
        imp.reload(modules)
        modules_old = [os.path.basename(inspect.getfile(m))[:-3]
                       for m in self.moduleList] 
        modules_all = modules.__all__
        new_modules_name = [m for m in modules_all if m not in modules_old]
        new_modules = []
        remove_modules = []

        # Load new modules
        for mod in new_modules_name:
            try:
                new_mod = importlib.import_module("." + mod, 
                                                  package="modules")
                new_modules.append(new_mod)
                self.irc.sendmsg(msg, "LOAD NEW MODULE {}".format(mod))
            except:
                self.irc.sendmsg(msg,
                                 "LOAD NEW MODULE {} FAILED".format(mod))

        # Reloads all known modules
        for mod in self.moduleList:
            moduleClass = getattr(mod, "Module")
            try:
                mod = imp.reload(mod)
            except:
                self.irc.sendmsg(msg, "RELOAD MODULE {} FAILED"
                                 .format(moduleClass))
                remove_modules.append(mod)
                traceback.print_exc()

        # Removes unloadable modules from known modules
        self.moduleList = [m for m in self.moduleList
                           if m not in remove_modules]
                
        self.moduleList = self.moduleList + new_modules
            
        self.irc.sendmsg(msg, "RELOADED MODULES FOLDER")
            
    # Each server command needs a function to handle itself, otherwise
    # it will catch a exception and print a not implemented error
    def handle(self, server_msg):
        try:
            getattr(self, "handle_{}".format(server_msg["CMD"]))(server_msg)
        except:
            print("CMD {} - NOT IMPLEMENTED".format(server_msg["CMD"]))
            print("prefix: {}\nparams: {}\ntrailing: {}"
                  .format(server_msg["PRE"], server_msg["PARAMS"], 
                          server_msg["MSG"]))

    # PING - Play PING PONG with the server
    def handle_PING(self, server_msg):
        self.irc.sendcmd("PONG", None, server_msg["MSG"])

    # RPL_ENDOFMOTD / ERR_NOMOTD - Finish joining server here
    def handle_376(self, server_msg):
        self.handle_422(server_msg)
    def handle_422(self, server_msg):
        extras = self.irc.EXTRAS
        for e in extras:
            self.irc.writeSocket(e)
        channels = self.irc.CHANNELS.split(",")
        for c in channels:
            self.irc.sendcmd("JOIN", None, c)
    
    # INVITE - Accept all channel invites automatically
    def handle_INVITE(self, server_msg):
        self.irc.sendcmd("JOIN", None, server_msg["MSG"])

    # PRIVMSG - Any sort of message
    def handle_PRIVMSG(self, server_msg):

        msg = {"FROM" : server_msg["PRE"],
               "TO" : server_msg["PARAMS"][0],
               "MSG" : server_msg["MSG"]}

        print("{} {}: {}".format(msg["TO"], msg["FROM"], msg["MSG"]))
        
        if msg["MSG"] == ".reload":
            self.reloadmodules(msg)

        if msg["MSG"][:5] == ".raw ":
            self.irc.sendraw(msg["MSG"][5:])
            
        for mod in self.moduleList:
            moduleClass = getattr(mod, "Module")
            if moduleClass.cmd == msg["MSG"][:len(moduleClass.cmd)]:
                try:
                    msg["MSG"] = msg["MSG"][len(moduleClass.cmd):].strip()
                    thread = moduleClass(msg, self.queue)
                    thread.start()
                except:
                    self.irc.sendmsg(msg, "MODULE {} FAILED"
                                     .format(moduleClass))

if __name__ == "__main__":
    
    AB = Bot("info")
    AB.run()
