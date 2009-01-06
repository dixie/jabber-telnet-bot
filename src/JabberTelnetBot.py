#!/usr/bin/env python
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
class UserMap:
    def __init__(self):
        self.user_map_by_telnet = {}
        self.user_map_by_jabber = {}
        
    def getJabberUser(self, user):
        return self.user_map_by_telnet.get(user.getID())
        
    def getTelnetUser(self, user):
        return self.user_map_by_jabber.get(user.getID())
        
    def addUserPair(self, userJabber, userTelnet):
        logging.info("Added new user pair Jabber=%s and Telnet=%s" % (userJabber.getID(), userTelnet.getID()))
        self.user_map_by_jabber[userJabber.getID()] = userTelnet
        self.user_map_by_telnet[userTelnet.getID()] = userJabber
        
    def removeUserPair(self, userJabber, userTelnet):
        logging.info("Remove user pair Jabber=%s and Telnet=%s" % (userJabber.getID(), userTelnet.getID()))
        del self.user_map_by_jabber[userJabber.getID()]
        del self.user_map_by_telnet[userTelnet.getID()]

class Bot:
    def __init__(self, atl_host, atl_port, jabber_jid, jabber_pwd, jabber_server,jabber_sasl):
        self.at = Telnet.Gateway(atl_host, atl_port)
        self.at.observe(self)
        self.at.start()
        self.jb = Jabber.Gateway(jabber_jid, jabber_pwd, jabber_server, jabber_sasl)
        self.jb.observe(self)
        self.users = UserMap()
    
    def handleTelnetMessage(self, user, msg):
        logging.debug("handle Telnet message")
        userJb = self.users.getJabberUser(user)
        if userJb == None:
            logging.error("No Jabber user for Telnet user found: %s" % user.getID())
        else:
            ansiText = Ansi.AnsiText(msg.getText())
            ansiText.setColorMap(COLOR_SCHEME)
            htmlText = ansiText.render()
            msgHTML = "<p style=\"font-family: courier\"><br/>%s</p> " % htmlText
            print("\n\n"+msgHTML+"\n\n")
            msgJb = Jabber.Message("Your IM don't support rich text messages",msgHTML)
            self.jb.send(userJb.getJabberUser(),msgJb,userJb.getThread(),userJb.getType())
            
    def handleTelnetDisconnect(self, user):
        logging.debug("Handle Telnet disconnect")
        userJb = self.users.getJabberUser(user)
        if userJb == None:
            logging.error("No Jabber user for Telnet user found: %s" % user.getID())
        else:
            txt = "Telnet Connection Lost"
            msgJb = Jabber.Message(txt,"<p style=\"font-weight: bold\">%s</p>" % txt)
            self.jb.send(userJb.getJabberUser(), msgJb)
            self.users.removeUserPair(userJb, user) 
        
    def handleJabberMessage(self, user, msg):
        logging.debug("Observing Jabber")
        userAt = self.users.getTelnetUser(user)
        if userAt == None:
            userAt = self.at.createUser()
            self.users.addUserPair(user, userAt)
        msgAt = Telnet.Message(str(msg.getText())+"\n")
        self.at.send(userAt, msgAt)
        
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
