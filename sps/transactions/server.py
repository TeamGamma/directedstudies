#!/usr/bin/env python

import re
import time
import eventlet
#import eventlet.patcher
#eventlet.patcher.monkey_patch()
import logging

from sps.transactions.commands import CommandHandler, CommandError
from sps.transactions import xml

log = logging.getLogger(__name__)

class TransactionServer(object):
    def __init__(self, address):
        self.address = address

        self.server = eventlet.listen(address)
        log.debug('Listening on %s', address)

        self.pool = eventlet.GreenPool()

    def start(self):
        log.debug('Starting server')
        eventlet.serve(self.server, self.handle_connection)

    def handle_connection(self, client, address):
        """
        Handle a single client connection.
        """

        log.info('New client: %s', address)

        # Read multiple lines from client and parse commands
        while True:
            line = client.recv(1000)

            if not line:
                log.info('Client disconnected')
                return

            log.debug('Request: %s' % repr(line))
            response = self.handle_line(line)

            log.debug('Response: %s' % repr(response))
            client.sendall(response + '\n')

    @staticmethod
    def handle_line(line):
        """ Handle a single line of input from a client and returns the string
        response. """

        command, args = TransactionServer.parse_line(line)

        try:
            handler = CommandHandler.get_handler(command)
            response = handler.run(*args)
        except CommandError, e:
            log.error(e)
            response = xml.ErrorResponse(e)
        except TypeError, e:
            log.error(e)
            response = xml.ErrorResponse(
                TypeError('Incorrect arguments for command "%s"' % command))
        except Exception, e:
            log.error('Unexpected error: %s' % e)
            response = xml.ErrorResponse(CommandError(e))

        return str(response)

    @staticmethod
    def parse_line(line):
        # Split by spaces or commas (Postel's Law!)
        tokens = re.split('[ ,]+', line.rstrip('\n\r'))
        command = tokens[0]
        args = tokens[1:]
        return command, args



