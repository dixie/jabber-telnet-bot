#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Jabber Telnet Bot, dixiecko@gmail.com 
#

import sys
import os
import xmpp.simplexml
import getopt
import logging

# This is necessary for loading some pretty modules in lib/dir 
sys.path.append(os.path.join(os.path.dirname(sys.argv[0]),"lib"))

import Jabber
import Telnet
import Ansi

#
# Default values which can be overwritten by configuration
# provided over command line. 
#

# Don't change values here but in external config.py 
# and that config as -c argument:
# 
# $ ./JabberAtlBot.py -c ./config.py
# 
# Telnet host/port
ATL_HOST="telnet.example.com"
ATL_PORT=23
# JID = login into Jabber / PWD = plain text password
JABBER_JID="meciar@example.com"
JABBER_PWD="nbusr123"
# This can be Set to None if JID contains all info
JABBER_SERVER=("jabber.example.com", 5223)
# JABBER_SERVER=None
enableTrace = False
# Configuration filename with path is config.py from directory where executed
# script is placed.
CONFIG_FILENAME=os.path.join(os.path.dirname(sys.argv[0]),"config.py")

# Color palete to be readable on the white background
COLOR_SCHEME = {
    'black' : 'black',
    'red' : 'red',
    'green' : 'darkgreen',
    'yellow' : 'darkyellow',
    'blue' : 'darkblue',
    'magenta' : 'magenta',
    'cyan' : 'darkcyan',
    'white' : 'black'
}


#
# Some useful code for us
#
class SessionMap:
    def __init__(self):
        self.session_map_by_telnet = {}
        self.session_map_by_jabber = {}
        
    def getJabberSession(self, session):
        return self.session_map_by_telnet.get(session.getID())
        
    def getTelnetSession(self, session):
        return self.session_map_by_jabber.get(session.getID())
        
    def addSessionPair(self, sessionJabber, sessionTelnet):
        logging.info("Added new session pair Jabber=%s and Telnet=%s" % (sessionJabber.getID(), sessionTelnet.getID()))
        self.session_map_by_jabber[sessionJabber.getID()] = sessionTelnet
        self.session_map_by_telnet[sessionTelnet.getID()] = sessionJabber
        
    def removeSessionPair(self, sessionJabber, sessionTelnet):
        logging.info("Remove session pair Jabber=%s and Telnet=%s" % (sessionJabber.getID(), sessionTelnet.getID()))
        del self.session_map_by_jabber[sessionJabber.getID()]
        del self.session_map_by_telnet[sessionTelnet.getID()]

class Bot:
    def __init__(self, atl_host, atl_port, jabber_jid, jabber_pwd, jabber_server,jabber_sasl):
        self.at = Telnet.Gateway(atl_host, atl_port)
        self.at.observe(self)
        self.at.start()
        self.jb = Jabber.Gateway(jabber_jid, jabber_pwd, jabber_server, jabber_sasl)
        self.jb.observe(self)
        self.sessions = SessionMap()
    
    def handleTelnetMessage(self, session, msg):
        logging.debug("handle Telnet message")
        sessionJb = self.sessions.getJabberSession(session)
        if sessionJb == None:
            logging.error("No Jabber session for Telnet session found: %s" % session.getID())
        else:
            ansiText = Ansi.AnsiText(msg.getText())
            ansiText.setColorMap(COLOR_SCHEME)
            htmlText = ansiText.render()
            pureText = ansiText.render(Ansi.RenderType.TEXT)
            msgHTML = "<p style=\"font-family: monospace\"><br/>%s</p> " % htmlText
            print("\n\n"+msgHTML+"\n\n")
            msgJb = Jabber.Message(pureText,msgHTML)
            self.jb.send(sessionJb.getJabberSession(),msgJb,sessionJb.getThread(),sessionJb.getType())
            
    def handleTelnetDisconnect(self, session):
        logging.debug("Handle Telnet disconnect")
        sessionJb = self.sessions.getJabberSession(session)
        if sessionJb == None:
            logging.error("No Jabber session for Telnet session found: %s" % session.getID())
        else:
            txt = "Telnet Connection Lost"
            msgJb = Jabber.Message(txt,"<p style=\"font-weight: bold\">%s</p>" % txt)
            self.jb.send(sessionJb.getJabberSession(), msgJb)
            self.sessions.removeSessionPair(sessionJb, session) 
        
    def handleJabberMessage(self, session, msg):
        logging.debug("handleJabberMessage")
        sessionAt = self.sessions.getTelnetSession(session)
        if sessionAt == None:
            sessionAt = self.at.createSession()
            self.sessions.addSessionPair(session, sessionAt)
	if msg.getText() != None:
            msgAt = Telnet.Message(msg.getText()+"\n")
            self.at.send(sessionAt, msgAt)
        else:
            print("Empty Text message received over Jabber")
            logging.error("Empty Text message received over Jabber")
        
    def serve(self):
        try:
            self.jb.serve_forever()
        finally:
            self.at.shutdown()

def showUsage():
    print("Usage: %s -c <config> [-v]" % sys.argv[0])
    print("    -c <config>   Configuration file")
    print("    -v            Enable verbose mode")
    print("    --help        For display of this help")
    print("")

#
# Main Code, Main Main Main
#
try:
        opts, args = getopt.getopt(sys.argv[1:], "c:v", ['help'])
except getopt.GetoptError, err:
        print(str(err))
        showUsage()
        sys.exit(2)

for o, a in opts:
        if o == "-v":
            enableTrace = True
        elif o in ("-c"):
            CONFIG_FILENAME = a
        elif o in ("--help"):
            showUsage()
            sys.exit(0)
        else:
            assert False, "Internal Error: unhandled option"

#
# Overwrite default configuration with values from the configuration file
#
print("Loading configuration from %s" % CONFIG_FILENAME)
execfile(CONFIG_FILENAME)

for pairs in [("HOST", ATL_HOST),("PORT", ATL_PORT), ("JABBERID",JABBER_JID)]:
    print("%s=%s" % pairs)

#
# Start the game
#
print("Starting.")
bot = Bot(ATL_HOST,ATL_PORT,JABBER_JID,JABBER_PWD,JABBER_SERVER,JABBER_SASL)
bot.serve()
print("Finished.")
