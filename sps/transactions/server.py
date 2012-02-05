#!/usr/bin/env python

import sys
import eventlet
import eventlet.patcher
eventlet.patcher.monkey_patch()

from sps.transactions import commands
from sps.transactions import database

class TransactionServer(object):
    # TODO: make CommandHandler and use method lookup instead
    commands = {
        'ECHO': commands.echo,
        'UPPERCASE': commands.uppercase,
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
            except commands.CommandError, e:
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


def run_server(port):
    # Setup server
    server = eventlet.listen(('0.0.0.0', port))
    transaction_server = TransactionServer()

    # Setup database pool
    session = database.get_session()

    print >> sys.stderr, 'Running transaction server on port %d' % port
    eventlet.serve(server, transaction_server.handle)

