
# TODO: make these into classes (for callbacks, etc.)

def echo(client, msg):
    return msg

def uppercase(client, msg):
    return msg.upper()

class CommandError(Exception):
    pass

