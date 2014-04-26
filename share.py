import queue
import sqlite3
import importlib
import threading

import modules

#### MESSAGE PASSING CLASS ####
###############################
# This class facilitates communication between the Bot and Modules
# It also contains variables that need to be shared between the two
#
# This class honestly introduces some race conditions but IRC has network delay, so it really shouldn't happen
class Share:
    
    def __init__(self, info):

        self.HOST = info["HOST"]
        self.PORT = info["PORT"]
        self.NICK = info["NICK"]
        self.IDENT = info["IDENT"]
        self.EXTRAS = info["EXTRAS"]
        self.REALNAME = info["REALNAME"]
        self.CHANNELS = info["CHANNELS"]

        self.queue = queue.Queue()

        self.modulelist = [importlib.import_module("." + mod, package="modules") for mod in modules.__all__]
        self.modulelist_lock = threading.Lock()

    def get_queue(self): return self.queue.get()
    def put_queue(self, msg): self.queue.put(msg)
    def empty_queue(self): return self.queue.empty()

    def get_modulelist(self): return self.modulelist
    def write_modulelist(self, modulelist):
        self.modulelist_lock.acquire()
        self.modulelist = modulelist
        self.modulelist_lock.release()
