import socket
import sys

HOST = 'localhost' # the remote host
PORT = 50008

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect ((HOST, PORT))

s.sendall('Hello World')

data = s.recv(1024)
s.close()
print 'Received', repr(data)


