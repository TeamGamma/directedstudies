#!/usr/bin/env python

import sys
import re
import eventlet
import eventlet.patcher
eventlet.patcher.monkey_patch()

from sps.transactions.commands import CommandHandler, CommandError, UnknownCommandError
from sps.transactions import database

class TransactionServer(object):

    def handle_connection(self, client, address):
        """ Handle a single client connection. """

        print 'New client:', address

        # Read multiple lines from client and parse commands
        while True:
            line = client.recv(1000)

            if not line:
                print 'Client disconnected'
                return

            print 'Request: %s' % repr(line)
            response = self.handle_line(line)

            print 'Response: %s' % repr(response)
            client.sendall(response)


    def handle_line(self, line):
        """ Handle a single line of input from a client """

        # Split by spaces or commas (Postel's Law!)
        tokens = re.split('[ ,]+', line[:-1])
        command = tokens[0]
        args = tokens[1:]

        try:
            handler = CommandHandler.get_handler(command)
            response = handler.run(*args)
        except UnknownCommandError:
            return 'Command does not exist\n'
        except TypeError, e:
            return 'Incorrect arguments for command "%s"\n' % command
        except Exception, e:
            print 'Unexpected error: %s\n' % e
            return 'Server Error\n'

        return response



def run_server(port):
    # Setup server
    server = eventlet.listen(('0.0.0.0', port))
    transaction_server = TransactionServer()

    print >> sys.stderr, 'Running transaction server on port %d' % port
    eventlet.serve(server, transaction_server.handle_connection)

