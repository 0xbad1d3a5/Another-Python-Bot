#!/usr/bin/python3
import os
import re
import sys
import imp
import copy
import time
import json
import queue
import inspect
import sqlite3
import traceback
import importlib
import threading
import http.client

import modules

from irc import IRC

### IRC MESSAGE PASSING CLASS ###
##############################
# This class facilitates communication between the Bot and Modules
# This class DOES NOT directly communicate with IRC, it only talks between
# the Bot and Module classes!
class Communication:
    
    def __init__(self):
        self.queue = queue.Queue()
        self.db_lock = threading.Lock()
        self.db_uri = "database.db"

    def put(self, msg):
        self.queue.put(msg)

    def get(self):
        return self.queue.get()

    def empty(self):
        return self.queue.empty()

    def lock(self):
        self.db_lock.acquire()
        
    def release(self):
        self.db_lock.release()

    def pretend(self):
        self.lock()
        time.sleep(5)
        self.release()

## IRC BOT CLASS ##
###################
# This class decides what to do with the messages from IRC
class Bot:
    
    def __init__(self, info_filename):

        self.moduleList = [importlib.import_module("." + mod, package="modules") for mod in modules.__all__]

        # Get settings from info file and connect the bot
        try:
            self.comm = Communication()
            self.info = json.load(open(info_filename, "r"))
            self.irc = IRC(self.info)
            self.irc.connect()
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
                try:
                    self.handle(server_msg)
                except:
                    traceback.print_exc()

            # Process responses from modules
            while not self.comm.empty():
                response = self.comm.get()
                self.sendmsg(response, response["MSG"])

    # Send a message to message origin on IRC
    def sendmsg(self, msg, string):
        # If it's a PM, then replace TO with sender
        # This is so we don't try to send messages to ourself
        if msg["TO"][:1] not in ['#', '$']:
            msg["TO"] = msg["FROM"][1:msg["FROM"].find("!")]
        self.irc.write(("PRIVMSG", msg["TO"]), string)

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
                self.sendmsg(msg, "LOAD NEW MODULE {}".format(mod))
            except:
                self.sendmsg(msg, "LOAD NEW MODULE {} FAILED".format(mod))

        # Reloads all known modules
        for mod in self.moduleList:
            moduleClass = getattr(mod, "Module")
            try:
                mod = imp.reload(mod)
            except:
                self.sendmsg(msg, "RELOAD MODULE {} FAILED"
                             .format(moduleClass))
                remove_modules.append(mod)
                traceback.print_exc()

        # Removes unloadable modules from known modules
        self.moduleList = [m for m in self.moduleList
                           if m not in remove_modules]
                
        self.moduleList = self.moduleList + new_modules
        self.sendmsg(msg, "RELOADED MODULES FOLDER")
            
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
        self.irc.write(("PONG",), server_msg["MSG"])

    # RPL_ENDOFMOTD / ERR_NOMOTD - Finish joining server here
    def handle_376(self, server_msg):
        self.handle_422(server_msg)
    def handle_422(self, server_msg):
        extras = self.irc.EXTRAS
        for e in extras:
            self.irc.write_raw(e)
        channels = self.irc.CHANNELS.split(",")
        for c in channels:
            self.irc.write(("JOIN",), c)
    
    # INVITE - Accept all channel invites automatically
    def handle_INVITE(self, server_msg):
        self.irc.write(("JOIN",), server_msg["MSG"])

    # PRIVMSG - Any sort of message
    def handle_PRIVMSG(self, server_msg):

        msg = {"FROM" : server_msg["PRE"],
               "TO" : server_msg["PARAMS"][0],
               "MSG" : server_msg["MSG"]}

        print("{} {}: {}".format(msg["TO"], msg["FROM"], msg["MSG"])
              .encode("utf-8"))
        
        if msg["MSG"] == ".reload":
            try:
                self.reloadmodules(msg)
            except:
                traceback.print_exc()

        if msg["MSG"][:5] == ".raw ":
            self.irc.write_raw(msg["MSG"][5:])
            
        for mod in self.moduleList:
            moduleClass = getattr(mod, "Module")
            if moduleClass.cmd == msg["MSG"][:len(moduleClass.cmd)]:
                try:
                    n_msg = copy.deepcopy(msg)
                    n_msg["MSG"] = msg["MSG"][len(moduleClass.cmd):].strip()
                    thread = moduleClass(n_msg, self.comm)
                    thread.start()
                except:
                    self.sendmsg(msg, "MODULE {} FAILED"
                                     .format(moduleClass))
                    traceback.print_exc()

if __name__ == "__main__":

    db = sqlite3.connect("data/database.db")

    print(sqlite3.sqlite_version)
    
    AB = Bot("infoc")
    AB.run()
