#!/usr/bin/env python

import Jabber
import sys
import re
import os.path

CMD_DIR=os.path.join(os.path.dirname(sys.argv[0]),"commands")

class JabberStupidBot(Jabber.Observer):
    def __init__(self, jabber_jid, jabber_pwd, jabber_server):
        self.jb = Jabber.Gateway(jabber_jid, jabber_pwd, jabber_server)
        self.jb.observe(self)
    
    def serve(self):
        self.jb.serve_forever()
    
    def handleJabberMessage(self, user, msg):
        print "Observing Jabber"
        # 1. zobrat prvu cast <pismena-cisla-pomlcka-undeskore....>
        # 2. zistit ci existuje command/<command>
        # 3. ak nie -> not supported command
        # 4. ak ano, spustit cez pexec() a vratit output
        msgTxt = msg.getText()
        if msgTxt == None:
            return
        
        ret = re.search("^([a-zA-Z0-9-_.]+) *(.*)", msg.getText())
        if ret == None:
            self.jb.send(user.getJabberUser(), Jabber.Message("Invalid command syntax"))
            return
        
        (cmd, arg) = (ret.group(1),ret.group(2))
        print("CMD=[%s] ARG=[%s]" % (cmd, arg))
        cmd = os.path.join(CMD_DIR, cmd)
        if os.path.isfile(cmd):
            process = os.popen(cmd + " " + arg)
            text = process.read()
            if len(text) == 0:
                text = "NO OUTPUT"
            process.close()
            print("OUTPUT=[%s]" % text)
            if text[0] == "<":
                print("It is RICH Text")
                self.jb.send(user.getJabberUser(), Jabber.Message("RichText", text))
            else:
                print("It is PLAIN Text")
                self.jb.send(user.getJabberUser(), Jabber.Message(text))
        else:
            self.jb.send(user.getJabberUser(), Jabber.Message("Not supported command"))

if len(sys.argv) != 2:
    print("Usage: %s <configuration file>" % sys.argv[0])
    sys.exit(1)        
        
print("Loading configuration from %s" % sys.argv[0])
execfile(sys.argv[1])

print("Starting.")
bot = JabberStupidBot(JABBER_JID,JABBER_PWD,JABBER_SERVER)
bot.serve()
print("Finished.")
