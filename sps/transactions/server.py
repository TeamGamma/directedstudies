#!/usr/bin/env python

import eventlet
import eventlet.patcher
eventlet.patcher.monkey_patch()
import logging
import re

from sps.transactions.commands import CommandHandler, CommandError
from sps.transactions import xml

log = logging.getLogger(__name__)

class TransactionServer(object):
    def __init__(self, address):
        self.address = address

        self.server = eventlet.listen(address, backlog=1000)
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
        client_in = client.makefile()

        # Read multiple lines from client and parse commands
        while True:
            line = client_in.readline()

            if not line:
                log.info('Client disconnected')
                return

            log.debug('Request: %s' % repr(line))
            response = self.handle_line(line)

            log.debug('Response: %s' % repr(response))
            try:
                client.sendall(response + '\n')
            except Exception, e:
                log.error(e)

    @staticmethod
    def handle_line(line):
        """ Handle a single line of input from a client and returns the string
        response. """

        command, args = TransactionServer.parse_line(line)

        try:
            handler = CommandHandler.get_handler(command)
            try:
                response = handler.run(*args)
            finally:
                # Make sure database sessions are closed no matter what
                if hasattr(handler, 'session'):
                    handler.session.close()
        except CommandError, e:
            log.error(e)
            response = xml.ErrorResponse(e)
        except TypeError, e:
            log.error(e)
            response = xml.ErrorResponse(
                TypeError('Incorrect arguments for command "%s"' % command))
        except Exception, e:
            log.error('Unexpected error: %s - %s' % (type(e), e))
            response = xml.ErrorResponse(CommandError(e))

        return str(response)

    @staticmethod
    def parse_line(line):
        # Split by spaces or commas (Postel's Law!)
        tokens = re.split('[ ,]+', line.rstrip('\n\r'))
        command = tokens[0]
        args = tokens[1:]
        return command, args



