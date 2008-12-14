#!/usr/bin/env python
import socket
import time
import sys

if len(sys.argv) != 2:
    print("Usage: %s <filename>" % sys.argv[0])
    sys.exit(1)

input = open(sys.argv[1], 'rb')
data = input.read()
input.close()

HOST = ''                 # Symbolic name meaning the local host
PORT = 7000	          # Arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
while 1:
    print("Waiting for connection on port %s" % PORT)
    conn, addr = s.accept()
    print("Connected by %s" % str(addr))
    print("Sending...")
    conn.send(data)
    time.sleep(10)
    conn.close()
    print("Done.")
