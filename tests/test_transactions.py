from tests.utils import unittest
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

class TestCommandNames(unittest.TestCase):
    pass

