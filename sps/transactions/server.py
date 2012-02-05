#!/usr/bin/env python

import sys
import eventlet
import eventlet.patcher
eventlet.patcher.monkey_patch()

from sps.transactions.commands import CommandHandler, CommandError, UnknownCommandError
from sps.transactions import database

class TransactionServer(object):
    def handle(self, client, address):
        """ Handles a single client """

        print 'New client:', address

        # Read multiple lines from client and parse command
        while True:
            line = client.recv(1000)

            if not line:
                print 'Client disconnected'
                return

            print 'Received: %s' % repr(line)
            tokens = line[:-1].split(' ')
            command = tokens[0]
            args = tokens[1:]

            try:
                handler = CommandHandler.get_handler(command)
                response = handler.run(*args)
            except UnknownCommandError:
                self.error(client, 'Command does not exist')
                return
            except TypeError, e:
                self.error(client, 'Incorrect arguments for command "%s"' % command)
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

    print >> sys.stderr, 'Running transaction server on port %d' % port
    eventlet.serve(server, transaction_server.handle)

