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
""" Parses a PRIVMSG into more useful parts

Message.FROM: ["FULL", "NICK", "USER", "HOST"]
Message.TO:   ["FULL", "NICK", "USER", "HOST"]
Message.MSG:  server_msg[3] (trailing part of a IRC message)
"""
class Message:

    nick_match = re.compile("(:(.*)!(.*)@(.*))|(.+)")

    def __init__(self, server_msg):
        self.FROM = self.parseName(server_msg[0])
        self.TO = self.parseName(server_msg[2][0])
        self.MSG = server_msg[3]

    def parseName(self, name):        
        s_name = re.search(Message.nick_match, name)        
        if s_name.group(5): return [s_name.group(0), s_name.group(5), "", ""]
        else: return [s_name.group(0), s_name.group(2), s_name.group(3), s_name.group(4)]
        
#### IRC BOT CLASS ####
#######################
""" This class handles parsed messages (pre, cmd, arg, msg) from IRC.getmsg()
"""
class Bot:
    
    def __init__(self, info_filename):
        try:
            info = json.load(open(info_filename, "r"))
            self.share = Share(info)
            self.irc = IRC(self.share.HOST, self.share.PORT)
        except:
            print("\"info\" file not found or syntax error")
            traceback.print_exc()
            sys.exit(1)

    """ Connect to the server by sending to IRC the required messages to initialize a connection
    """
    def connect(self):
        self.sendcmd(("NICK", self.share.NICK))
        self.sendcmd(("USER", self.share.IDENT, "0", "*"), self.share.REALNAME)
        
    def run(self):
        while True:
            # Sleep so we don't eat the CPU alive
            time.sleep(0.05)
            # Handle module commands
            server_msg = self.irc.getmsg()
            if server_msg:
                try: self.handle(server_msg)
                except: traceback.print_exc()
            # Process responses from modules
            while not self.share.empty_queue():
                response = self.share.get_queue()
                self.sendcmd(response[0], response[1])

    def send(self, string):
        self.irc.write(string + "\r\n")

    def sendcmd(self, cmd, text=None):
        temp = ' '.join(cmd)
        if text: temp = "{} :{}".format(temp, text)[:510]
        self.send(temp)

    def sendmsg(self, msg, string):
        if self.share.NICK == msg.TO[1]: msg.TO[1] = msg.FROM[1]
        sendcmd(("PRIVMSG", msg.TO[1]), string)        

    # Try to run our modules
    def runmodules(self, msg):
        for mod in self.share.get_modulelist():
            moduleClass = getattr(mod, "Module")
            modcmd = None
            modregex = None
            
            try: modcmd = moduleClass.cmd 
            except: pass 
            try: modregex = moduleClass.regex 
            except: pass
            
            if modcmd:
                if modcmd == msg.MSG[:len(moduleClass.cmd)]:
                    try:
                        n_msg = copy.deepcopy(msg)
                        n_msg.MSG = msg.MSG[len(modcmd):]
                        thread = moduleClass(n_msg, self.share)
                        thread.start()
                    except:
                        self.sendcmd(("PRIVMSG", msg.TO[1]), "MODULE {} FAILED".format(moduleClass))
                        traceback.print_exc()
            elif modregex:
                if re.search(modregex, msg.MSG):
                    try:
                        n_msg = copy.deepcopy(msg)
                        thread = moduleClass(n_msg, self.share)
                        thread.start()
                    except:
                        self.sendmsg(("PRIVMSG", msg.TO[1]), "MODULE {} FAILED".format(moduleClass))
                        traceback.print_exc()

    def handle(self, server_msg):
        try:
            getattr(self, "handle_{}".format(server_msg[1]))(server_msg)
        except:
            print("CMD {} - NOT IMPLEMENTED".format(server_msg[1]))
            print("prefix: {}\nparams: {}\ntrailing: {}".format(server_msg[0], server_msg[2], server_msg[3]))
            #traceback.print_exc()

    # PING - Play PING PONG with the server
    def handle_PING(self, server_msg):
        self.sendcmd(("PONG",), server_msg[3])

    # RPL_ENDOFMOTD / ERR_NOMOTD - Finish joining server here
    def handle_376(self, server_msg):
        self.handle_422(server_msg)
    def handle_422(self, server_msg):
        extras = self.share.EXTRAS
        for e in extras: self.send(e)
        channels = self.share.CHANNELS.split(",")
        for c in channels: self.sendcmd(("JOIN",), c)
    
    # INVITE - Accept all channel invites automatically
    def handle_INVITE(self, server_msg):
        print(server_msg)
        self.sendcmd(("JOIN",), server_msg[3])

    # PRIVMSG - Any sort of message
    def handle_PRIVMSG(self, server_msg):
        print(server_msg)
        try:
            msg = Message(server_msg)
            self.runmodules(msg)
        except:
            traceback.print_exc()
        print("{} {}: {}".format(msg.TO[0], msg.FROM[0], msg.MSG).encode("utf-8"))

if __name__ == "__main__":

    AB = Bot("info")
    AB.connect()
    AB.run()
