import queue
import sqlite3
import threading

#### MESSAGE PASSING CLASS ####
###############################
# This class facilitates communication between the Bot and Modules
# It also contains variables that need to be shared between the two
class Share:
    
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
