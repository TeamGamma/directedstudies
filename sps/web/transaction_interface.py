import socket

#HOST = 'localhost' # the remote host
#PORT = 50008

def send(HOST, PORT, message):

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    s.sendall(message + '\n')

    # Read an entire line of variable length
    confirmation_msg = s.makefile().readline()
    s.close()

    return confirmation_msg

