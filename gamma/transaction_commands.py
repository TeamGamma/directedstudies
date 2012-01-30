import socket

# TODO: make these into classes (for callbacks, etc.)

def echo(client, msg):
    return msg

def uppercase(client, msg):
    return msg.upper()

def whoami(client, msg):
    return str(socket.getsockname(client))

class CommandError(Exception):
    pass

