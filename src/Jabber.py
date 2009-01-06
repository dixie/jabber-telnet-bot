# Jabber Gateway Implementation

import xmpp
import xmpp.simplexml
import inspect
import string

class HTMLMessage(xmpp.Message):
    """ XMPP Message stanza - "push" mechanism."""
    def __init__(self, to=None, body=None, typ=None, subject=None, richBody=None):
        """ Create message object. You can specify recipient, text of message, type of message
            any additional attributes, sender of the message, any additional payload (f.e. jabber:x:delay element) and namespace in one go.
            Alternatively you can pass in the other XML object as the 'node' parameted to replicate it as message. """
        xmpp.Message.__init__(self, to, body, typ, subject)
        if richBody != None:
            content = xmpp.simplexml.XML2Node(richBody)
            self.setTag('html', namespace='http://jabber.org/protocol/xhtml-im')
            html = self.getTag('html')
            html.setTag('body', namespace='http://www.w3.org/1999/xhtml')
            body = html.getTag('body')
            body.addChild(node=content)
        print(str(self))

class User:
    def __init__(self,user,thread,atype):
        self.user = user
        self.thread = thread
        self.atype = atype
        
    def getID(self):
        return self.user.getStripped()  
    
    def getJabberUser(self):
        return self.user
    
    def getType(self):
        return self.atype
    
    def getThread(self):
        return self.thread

class Message:
    def __init__(self,body=None,richBody=None):
        self.body = body
        self.richBody = richBody
        
    def getText(self):
        return self.body
    
    def getRichText(self):
        return self.richBody

class Observer:
    def handleJabberMessage(self, user, message):
        print("Observing")
    
class Gateway:
    def __init__( self, jid, password, server = None, saslParam = 1, res = None):
        self.jid = xmpp.JID( jid)
        self.password = password
        self.res = (res or self.__class__.__name__)
        self.conn = None
        self.__finished = False
        self.observers = []
        self.server = server
	self.sasl = saslParam
        
    def log( self, s):
        """Logging facility, can be overridden in subclasses to log to file, etc.."""
        print '%s: %s' % ( self.__class__.__name__, s, )

    def connect( self):
        if not self.conn:
            conn = xmpp.Client( self.jid.getDomain(), debug = ['always', 'browser', 'testcommand'])
               
            if self.server == None:
                if not conn.connect():
                    self.log( 'unable to connect to server.')
                    return None
            elif not conn.connect(self.server):
                self.log( 'unable to connect to server.')
                return None
                
            if not conn.auth( self.jid.getNode(), self.password, self.res, sasl=self.sasl):
                self.log( 'unable to authorize with server.')
                return None
            
            conn.RegisterHandler( 'message', self.callback_message)
            conn.RegisterHandler( 'presence', self.callback_presence)
            conn.sendInitPresence()
            self.conn = conn
        return self.conn

    def quit(self):
        self.__finished = True

    def send(self, user, msg, thread=None, atype=None):
        """Sends a simple message to the specified user."""
        mess = HTMLMessage( user, msg.getText(), richBody=msg.getRichText())
        if thread and atype:
            mess.setThread(thread)
            mess.setType(atype)
        self.connect().send( mess)

    def callback_message( self, conn, mess):
        """Messages sent to the bot will arrive here. Command handling + routing is done in this function."""
        print("callback_message method")
        msg = Message(mess.getBody())
        usr = User(mess.getFrom(),mess.getThread(), mess.getType())
        for observer in self.observers:
            observer.handleJabberMessage(usr,msg)
            
    def callback_presence(self, conn, mess):
        """Presence arrived"""
        print("callback_presence")
        type = mess.getType()
        if type == "subscribe":
            jid = str(mess.getFrom())
            print("Authorize JID=%s" % jid)
            self.conn.Roster.Authorize(jid)
        else:
            print("This type of presence not handled: " + str(type))
        
    def idle_proc(self):
        """This function will be called in the main loop."""
        pass

    def serve_forever( self, connect_callback = None, disconnect_callback = None):
        """Connects to the server and handles messages."""
        conn = self.connect()
        if conn:
            self.log('bot connected. serving forever.')
        else:
            self.log('could not connect to server - aborting.')
            return
        while not self.__finished:
            try:
                conn.Process(1)
                self.idle_proc()
            except KeyboardInterrupt:
                self.log('bot stopped by user request. shutting down.')
                break
    
    def observe(self,observer):
        self.observers.append(observer)
        print "Observer registered"
