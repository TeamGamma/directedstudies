#!/usr/bin/env python

import eventlet
from transaction_commands import echo, uppercase
from transaction_commands import CommandError

class TransactionServer(object):
    commands = {
        'ECHO': echo,
        'UPPERCASE': uppercase,
    }

    def handle(self, client, address):
        """ Handles a single client """

        print 'New client:', address

        # Read multiple lines from client and parse command
        while True:
            line = client.recv(1000)
            if not line:
                print 'Client disconnected'
                return
            try:
                print 'Received:' + repr(line.split(' ', 1))
                command, args = line.split(' ', 1)
            except ValueError, e:
                self.error(client, 'Invalid command - %s' % e)
                return

            try:
                response = self.commands[command](client, args)
            except KeyError:
                self.error(client, 'Command does not exist')
                return
            except CommandError, e:
                self.error(client, e)
                return
            except Exception, e:
                print 'Unexpected error: %s' % e
                self.error(client, 'Server Error')
                return

            client.sendall(response)

    def error(self, client, msg):
        print msg
        client.sendall('ERROR: %s' % (msg,))



server = eventlet.listen(('0.0.0.0', 6000))
pool = eventlet.GreenPool(10000)
transaction_server = TransactionServer()

eventlet.serve(server, transaction_server.handle)

