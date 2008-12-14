import threading
import os
import time
import select
import socket
import sys

#
# 
#
# Following Telnet data -> jabber message flush policy is defined:
# if(not new data comming from Telnet for more than SILENT_FLUSH_TIME) 
#         flushData -> send data over jabber to user
# else if (data are still comming but not flushed for FORCE_FLUSH_TIME)
#         flushData -> send data over jabber to user
#
# In human words:
# Means that data (lines) are grouped for 10 seconds and than they
# are written to Jabber as message. But if there is no new data for
# 4 seconds, then they will be send immediatly (without waiting for
# next two seconds).

# These values are defined in seconds 
FORCE_FLUSH_TIME = 6
FORCE_FLUSH_SIZE = 80*30
SILENT_FLUSH_TIME = 2

#
# Telnet User
#
class User:
    def __init__(self, userId, sock):
        self.userId = "%s@Telnet" % userId
        self.sock = sock
        self.timestamp_flush = time.time()
        self.timestamp_mod = time.time()
        self.buffer = ""
        print "User initialized"
        
    def getID(self):
        return self.userId
        
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
        buff = self.buffer
        self.buffer = ""
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
	if len(self.buffer) > FORCE_FLUSH_SIZE:
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
    def handleTelnetMessage(self, user, text):
        print "Handling Telnet Message"
    
    def handleTelnetDisconnect(self, user):
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
        self._userId = 0;
        self.map_sock_to_user = {}
        
    def run(self):
        print("Telnet Thread started")
        while self.stopFlag == False:
            #print("Processing clients. active users: %s" % (len(self.map_sock_to_user)))
            socketList = []
            for user in self.map_sock_to_user.values():
                socketList.append(user.getSocket())
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
                    user = self.map_sock_to_user[sock]
                    for observer in self.observers:
                        observer.handleTelnetDisconnect(user)
                        del self.map_sock_to_user[sock]
                elif len(buffer) == 0:
                    print('Warning: sock.rev() returns empty data!')
                else:
                    user = self.map_sock_to_user[sock]
                    user.appendBuffer(buffer)
            #
            # Check if we need to flush buffers
            #
            for user in self.map_sock_to_user.values():
                if user.needFlush():
                    msg = Message(user.flushBuffer())
                    for observer in self.observers:
                        observer.handleTelnetMessage(user, msg)

            #
            # Handle error sockets
            #
            for sock in ready[2]:
                print "Handle disconnected user (exception event on select())"
                user = self.map_sock_to_user[sock]
                for observer in self.observers:
                    observer.handleTelnetDisconnect(user)
                    del self.map_sock_to_user[sock]
       
    #
    # Method for sending message to Telnet User
    #
    def send(self, user, message):
        print("Sending message to user=%s message=%s" % (user.getID(), message.getText()))
        sock = user.getSocket()
        if not self.map_sock_to_user.has_key(sock):
            print("No such Telnet user found!")
        else:
            sock.send(message.getText())
       
    #
    # Create new Telnet connection (user)
    #
    def createUser(self):
        self._userId+=1
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))
        newUser = User(self._userId, sock)
        self.map_sock_to_user[sock] = newUser
        return newUser
        
    def shutdown(self):
        self.stopFlag = True
   
    #
    # Register Telnet events observer (callback)
    #
    def observe(self, observer):
        print "Registered Telnet Observer"
        self.observers.append(observer)
