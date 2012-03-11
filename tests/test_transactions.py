from tests.utils import unittest
from sps.transactions.commands import CommandHandler, CommandError
from sps.transactions.server import TransactionServer


class TestParseLine(unittest.TestCase):
    def setUp(self):
        self.server = TransactionServer(('', 0))

    def test_returns_command_and_args(self):
        res = self.server.parse_line('COMMAND,arg1,arg2')
        self.assertEqual(len(res), 2)
        self.assertEqual(len(res[1]), 2)

    def test_comma_input(self):
        command, args = self.server.parse_line('COMMAND,arg1,arg2')
        self.assertEqual(command, 'COMMAND')
        self.assertEqual(args[0], 'arg1')
        self.assertEqual(args[1], 'arg2')

    def test_space_input(self):
        command, args = self.server.parse_line('COMMAND arg1 arg2')
        self.assertEqual(command, 'COMMAND')
        self.assertEqual(args[0], 'arg1')
        self.assertEqual(args[1], 'arg2')

class TestTransactionsErrorResponse(unittest.TestCase):
    def setUp(self):
        """
        Override CommandHandler.get_handler with a factory for functions that
        raise a predefined exception.
        """
        self.exception = Exception()

        def fake_get_handler(*args):
            def handler(*args):
                raise self.exception
        self.original_get_handler = CommandHandler.get_handler
        CommandHandler.get_handler = fake_get_handler

    def tearDown(self):
        CommandHandler.get_handler = self.original_get_handler

    def test_commanderror_newline(self):
        """ When a command throws a CommandError, there should be no newlines
        in the response. """
        self.exception = CommandError('stuff')
        response = TransactionServer.handle_line('a,b')
        self.assertEqual(response.count('\n'), 0)

    def test_typeerror_error_newline(self):
        """ When a command throws a TypeError, there should be no newlines
        in the response. """
        self.exception = TypeError('stuff')
        response = TransactionServer.handle_line('a,b')
        self.assertEqual(response.count('\n'), 0)

    def test_exception_error_newline(self):
        """ When a command throws any other Exception, there should be no
        newlines in the response. """
        self.exception = Exception('stuff')
        response = TransactionServer.handle_line('a,b')
        self.assertEqual(response.count('\n'), 0)



