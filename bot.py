#!/usr/bin/python3
import sys
import re
import socket
import http.client
import urllib.parse
import math
import traceback

from time import sleep

## This is the class that will communicate with the IRC server ##
#################################################################
class irc:
    
    # info is a dictionary containing connection information
    def __init__(self, info):
        
        self.HOST = info["HOST"]
        self.PORT = info["PORT"]
        self.CHANNELS = info["CHANNELS"]
        self.NICK = info["NICK"]
        self.IDENT = info["IDENT"]
        self.REALNAME = info["REALNAME"]
        self.EXTRA = info["EXTRA"]

## MAIN PROGRAM ##
##################

# First thing we need to do is check for the info file
try:
    f = open("info", "r")
except IOError:
    print("File Not Found: \"info\"")
    sys.exit(1)

# Get settings from file
info = {}
for l in f:
    (key, val) = l.strip("\n").split("=")
    info[key.upper()] = val

# Create a new irc object
try:
    s = irc(info)
except KeyError:
    print("Error in info file")
    sys.exit(1)
