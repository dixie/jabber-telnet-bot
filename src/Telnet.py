import threading
import os
import time
import select
import socket
import string
import sys

#
# 
#
# Following Telnet data -> jabber message flush policy is defined:
# if(not new data comming from Telnet for more than SILENT_FLUSH_TIME) 
#         flushData -> send data over jabber to session
# else if (data are still comming but not flushed for FORCE_FLUSH_TIME)
#         flushData -> send data over jabber to session
#
# In human words:
# Means that data (lines) are grouped for 10 seconds and than they
# are written to Jabber as message. But if there is no new data for
# 4 seconds, then they will be send immediatly (without waiting for
# next two seconds).

# These values are defined in seconds 
FORCE_FLUSH_TIME = 6
FORCE_FLUSH_LINES = 3
SILENT_FLUSH_TIME = 2

#
# Telnet Session
#
class Session:
    def __init__(self, sessionId, sock):
        self.sessionId = "%s@Telnet" % sessionId
        self.sock = sock
        self.timestamp_flush = time.time()
        self.timestamp_mod = time.time()
        self.buffer = ""
        print "Session initialized"
        
    def getID(self):
        return self.sessionId
        
    def getSocket(self):
        return self.sock
       
    #
    # Append text data into buffer
    #
    def appendBuffer(self, text):
        self.buffer += text
        self.timestamp_mod = time.time()
       
    #
    # Method returns internal buffer data
    # and empty buffer at same time
    #
    def flushBuffer(self):
        lines = string.split(self.buffer, '\n')
        if(len(lines) >= FORCE_FLUSH_LINES):
            self.buffer = lines.pop()
        else:
            self.buffer = ""
        buff = '\n'.join(lines)
        self.timestamp_flush = time.time()
        self.timestamp_mod = time.time()
        return buff

    def needFlush(self):
        if len(self.buffer) == 0:
            self.timestamp_flush = time.time()
            return False
        timeNow = time.time()
        # Send data if there is more than 1 seconds
        # silent on the Telnet (no more data comming)
        if(timeNow - self.timestamp_mod > SILENT_FLUSH_TIME):
            return True
        # In the case of continuing output, send that 
        # after FORCE_FLUSH_TIME window
        if(timeNow - self.timestamp_flush > FORCE_FLUSH_TIME):
            return True
        # In the case of the big buffer, flush immediatly
        if len(string.split(self.buffer, '\n')) > FORCE_FLUSH_LINES:
            return True
        return False
       
#
# Telnet Message
#
class Message:
    def __init__(self, text):
        self.text = text
        
    def getText(self):
        return self.text

#
# Example observer implementation
#
class Observer:
    def handleTelnetMessage(self, session, text):
        print "Handling Telnet Message"
    
    def handleTelnetDisconnect(self, session):
        print "Handling Telnet Disconnect"
       
#
# Telnet GW 
#
class Gateway(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.stopFlag = False
        self.observers = []
        self._sessionId = 0;
        self.map_sock_to_session = {}
        
    def run(self):
        print("Telnet Thread started")
        while self.stopFlag == False:
            #print("Processing clients. active sessions: %s" % (len(self.map_sock_to_session)))
            socketList = []
            for session in self.map_sock_to_session.values():
                socketList.append(session.getSocket())
            #
            # Wait for READ / ERROR Event (hardcoded delay 1 seconds)
            #
            ready = select.select(socketList,[],socketList, 1)
           
            # Some traces
            if len(ready[0]) > 0:
                print(" Sockets count Ready for Read = %s" % (len(ready[0])))
            if len(ready[2]) > 0:
                print(" Sockets count Ready for Error = %s" % (len(ready[2])))
           
            for sock in ready[0]:
                buffer = sock.recv(90,socket.MSG_DONTWAIT)
                if not buffer:
                    session = self.map_sock_to_session[sock]
                    for observer in self.observers:
                        observer.handleTelnetDisconnect(session)
                        del self.map_sock_to_session[sock]
                elif len(buffer) == 0:
                    print('Warning: sock.rev() returns empty data!')
                else:
                    session = self.map_sock_to_session[sock]
                    session.appendBuffer(buffer)
            #
            # Check if we need to flush buffers
            #
            for session in self.map_sock_to_session.values():
                if session.needFlush():
                    msg = Message(session.flushBuffer())
                    for observer in self.observers:
                        observer.handleTelnetMessage(session, msg)

            #
            # Handle error sockets
            #
            for sock in ready[2]:
                print "Handle disconnected session (exception event on select())"
                session = self.map_sock_to_session[sock]
                for observer in self.observers:
                    observer.handleTelnetDisconnect(session)
                    del self.map_sock_to_session[sock]
       
    #
    # Method for sending message to Telnet Session
    #
    def send(self, session, message):
        print("Sending message to session=%s message=%s" % (session.getID(), message.getText()))
        sock = session.getSocket()
        if not self.map_sock_to_session.has_key(sock):
            print("No such Telnet session found!")
        else:
            sock.send(message.getText())
       
    #
    # Create new Telnet connection (session)
    #
    def createSession(self):
        self._sessionId+=1
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))
        newSession = Session(self._sessionId, sock)
        self.map_sock_to_session[sock] = newSession
        return newSession
        
    def shutdown(self):
        self.stopFlag = True
   
    #
    # Register Telnet events observer (callback)
    #
    def observe(self, observer):
        print "Registered Telnet Observer"
        self.observers.append(observer)
