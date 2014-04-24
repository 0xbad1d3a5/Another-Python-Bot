#!/usr/bin/python3
import re
import sys
import copy
import time
import json
import queue
import inspect
import sqlite3
import traceback
import threading
import http.client

from share import Share
from irc import IRC

#### MESSAGE CLASS ####
#######################
class Message:

    def __init__(self, server_msg):
        
        nick_match = re.compile("(:(.*)!(.*)@(.*))|(.+)")
        
        from_name = re.search(nick_match, server_msg["PRE"])
        to_name = re.search(nick_match, server_msg["PARAMS"][0])

        self.from_nick = ""
        self.from_user = ""
        self.from_host = ""
        self.to_nick = ""
        self.to_user = ""
        self.to_host = ""
        self.msg = server_msg["MSG"]
        
        if from_name.group(5):
            self.from_nick = from_name.group(5)
        else:
            self.from_nick = from_name.group(2)
            self.from_user = from_name.group(3)
            self.from_host = from_name.group(4)
        
        if to_name.group(5):
            self.to_nick = to_name.group(5)
        else:
            self.to_nick = to_name.group(2)
            self.to_nick = to_name.group(3)
            self.to_nick = to_name.group(4)
        
#### IRC BOT CLASS ####
#######################
# This class decides what to do with the messages from IRC
class Bot:
    
    def __init__(self, info_filename):

        # Get settings from info file and connect the bot
        try:
            # Load info file
            info = json.load(open(info_filename, "r"))
            # Set variables
            self.HOST = info["HOST"]
            self.PORT = int(info["PORT"])
            self.CHANNELS = info["CHANNELS"]
            self.NICK = info["NICK"]
            self.IDENT = info["IDENT"]
            self.REALNAME = info["REALNAME"]
            self.EXTRAS = info["EXTRAS"]
            # Make socket
            self.irc = IRC(self.HOST, self.PORT)
            # Connect to IRC
            self.connect()
            # Initialize Share class
            self.share = Share()
        except:
            print("\"info\" file not found or syntax error")
            traceback.print_exc()
            sys.exit(1)

    def run(self):

        while True:

            # Sleep so we don't eat the CPU alive
            time.sleep(0.05)
            
            # Handle IRC commands
            server_msg = self.irc.getmsg()
            if server_msg:
                try: self.handle(server_msg)
                except: traceback.print_exc()

            # Process responses from modules
            while not self.share.empty():
                response = self.share.get()
                self.sendmsg(response, response["MSG"])

    # Connect to the server using the information given
    def connect(self):
        self.irc.write(("NICK", self.NICK))
        self.irc.write(("USER", self.IDENT, "0", "*"), self.REALNAME)

    # Send a message to message origin on IRC
    def sendmsg(self, msg, string):
        # If it's a PM, then replace TO with sender
        # This is so we don't try to send messages to ourself
        if msg["TO"][:1] not in ['#', '$']:
            msg["TO"] = msg["FROM"][1:msg["FROM"].find("!")]
        self.irc.write(("PRIVMSG", msg["TO"]), string)

    # Try to run our modules
    def runmodules(self, msg):

        for mod in self.share.moduleList:
            
            moduleClass = getattr(mod, "Module")

            modcmd = None
            modregex = None
            
            try: modcmd = moduleClass.cmd 
            except: pass 
            try: modregex = moduleClass.regex 
            except: pass
            
            if modcmd:
                if modcmd == msg["MSG"][:len(moduleClass.cmd)]:
                    try:
                        n_msg = copy.deepcopy(msg)
                        n_msg["MSG"] = msg["MSG"][len(modcmd):].strip()
                        thread = moduleClass(n_msg, self.share)
                        thread.start()
                    except:
                        self.sendmsg(msg, "MODULE {} FAILED".format(moduleClass))
                        traceback.print_exc()

            elif modregex:
                if re.search(modregex, msg["MSG"]):
                    try:
                        n_msg = copy.deepcopy(msg)
                        thread = moduleClass(n_msg, self.share)
                        thread.start()
                    except:
                        self.sendmsg(msg, "MODULE {} FAILED".format(moduleClass))
                        traceback.print_exc()

    # Each server command needs a function to handle itself, otherwise
    # it will catch a exception and print a not implemented error.
    # 
    # To handle a command, simply define the function:
    # handle_CMD, replacing CMD with the IRC command in this class.
    # For example, the function handle_PRIVMSG(self, server_msg) will
    # be triggered if we recieve a PRIVMSG from the server.
    def handle(self, server_msg):
        try:
            getattr(self, "handle_{}".format(server_msg["CMD"]))(server_msg)
        except:
            print("CMD {} - NOT IMPLEMENTED".format(server_msg["CMD"]))
            #print("prefix: {}\nparams: {}\ntrailing: {}"
            #      .format(server_msg["PRE"], server_msg["PARAMS"], server_msg["MSG"]))
            #traceback.print_exc()

    # PING - Play PING PONG with the server
    def handle_PING(self, server_msg):
        self.irc.write(("PONG",), server_msg["MSG"])

    # RPL_ENDOFMOTD / ERR_NOMOTD - Finish joining server here
    def handle_376(self, server_msg):
        self.handle_422(server_msg)
    def handle_422(self, server_msg):
        extras = self.EXTRAS
        for e in extras:
            self.irc.write_raw(e)
        channels = self.CHANNELS.split(",")
        for c in channels:
            self.irc.write(("JOIN",), c)
    
    # INVITE - Accept all channel invites automatically
    def handle_INVITE(self, server_msg):
        self.irc.write(("JOIN",), server_msg["MSG"])

    # PRIVMSG - Any sort of message
    def handle_PRIVMSG(self, server_msg):
        
        print(server_msg)
        
        try:
            msg = Message(server_msg)
        except:
            traceback.print_exc()
        
        msg = {"FROM" : server_msg["PRE"],
               "TO" : server_msg["PARAMS"][0],
               "MSG" : server_msg["MSG"]}
        self.runmodules(msg)

        if msg["MSG"][:5] == ".raw ": self.irc.write_raw(msg["MSG"][5:])
            
        print("{} {}: {}".format(msg["TO"], msg["FROM"], msg["MSG"]).encode("utf-8"))


if __name__ == "__main__":

    AB = Bot("info")
    AB.run()
        
