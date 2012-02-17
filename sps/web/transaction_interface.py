import socket
import sys

#HOST = 'localhost' # the remote host
#PORT = 50008

def send(HOST, PORT, message):
 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect ((HOST, PORT))

    s.sendall(message)

    confirmation_msg = s.recv(1024)
    s.close()
    print 'Received', repr(confirmation_msg)
    return True

if __name__ =='__main__':
    print 'you just ran the transaction interface'
