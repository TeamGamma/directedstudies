#!/usr/bin/env python

import sys
import re
import time
import eventlet
import eventlet.patcher
eventlet.patcher.monkey_patch()

from sps.transactions.commands import CommandHandler, UnknownCommandError
from sps.transactions import database

class TransactionServer(object):
    def __init__(self, address):
        self.address = address

        self.server = eventlet.listen(address)
        self.pool = eventlet.GreenPool()

    def start(self):
        eventlet.serve(self.server, self.handle_connection)

    def timer_test(self, timeout):
        time.sleep(timeout)
        print '%d seconds since connection started!' % timeout

    def handle_connection(self, client, address):
        """
        Handle a single client connection.
        """

        print 'New client:', address
        self.pool.spawn_n(self.timer_test, 10)

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



def run_server(port, autoreload=False):
    if(autoreload):
        from sps.utils.autoreload_eventlet import autoreload
        try:
            autoreload()
        except:
            exit(0)

    print >> sys.stderr, 'Starting transaction server on port %d' % port
    transaction_server = TransactionServer(('0.0.0.0', port))
    try:
        transaction_server.start()
    except KeyboardInterrupt:
        print >> sys.stderr, '\nInterrupted'

if __name__ == '__main__':
    run_server(6000)

